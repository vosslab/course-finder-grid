import AppKit
import CoreServices
import Darwin
import Foundation
import OSAKit

private let requestVersion = 1
private let maximumRequestBytes: off_t = 1_100_000
private let maximumSubjectBytes = 512
private let maximumBodyBytes = 1_000_000
private let maximumAttachmentBytes: off_t = 50_000_000
private let allowedRecipients = Set([
	"nvoss@roosevelt.edu",
	"rseiser@roosevelt.edu",
])

private let mailScriptSource = """
on sendMessage(recipientAddresses, messageSubject, messageBody, attachmentPath)
	tell application "Mail"
		activate
		delay 3
		set theMessage to make new outgoing message with properties {subject:messageSubject, content:messageBody, visible:true}
		tell theMessage
			repeat with recipientAddress in recipientAddresses
				make new to recipient with properties {address:(recipientAddress as text)}
			end repeat
			if attachmentPath is not "" then
				set theAttachment to POSIX file attachmentPath
				make new attachment with properties {file name:theAttachment} at after the last paragraph
			end if
			delay 2
			send
		end tell
	end tell
	return "sent"
end sendMessage
"""

private struct MailRequest: Decodable {
	let version: Int
	let recipients: [String]
	let subject: String
	let body: String
	let attachmentPath: String?

	enum CodingKeys: String, CodingKey {
		case version
		case recipients
		case subject
		case body
		case attachmentPath = "attachment_path"
	}
}

private struct MailResult: Encodable {
	let status: String
	let error: String?
}

private enum MailerFailure: Error, CustomStringConvertible {
	case message(String)

	var description: String {
		switch self {
		case let .message(message):
			return message
		}
	}
}

// ASVS 2.2.1 and 15.3.5: reject malformed, oversized, or wrongly owned files
// before decoding any request fields.
private func checkedStatus(for path: String, expectedType: mode_t) throws -> stat {
	var fileStatus = stat()
	if lstat(path, &fileStatus) != 0 {
		throw MailerFailure.message("The mail request is unavailable.")
	}
	if (fileStatus.st_mode & S_IFMT) != expectedType {
		throw MailerFailure.message("The mail request has an invalid file type.")
	}
	if fileStatus.st_uid != getuid() {
		throw MailerFailure.message("The mail request has an invalid owner.")
	}
	return fileStatus
}

private func validateRequestLocation(_ requestURL: URL) throws {
	let parentURL = requestURL.deletingLastPathComponent()
	let parentStatus = try checkedStatus(for: parentURL.path, expectedType: S_IFDIR)
	if (parentStatus.st_mode & 0o077) != 0 {
		throw MailerFailure.message("The mail request directory is not private.")
	}
	if !parentURL.lastPathComponent.hasPrefix("course_finder_mailer_") {
		throw MailerFailure.message("The mail request directory is invalid.")
	}

	let temporaryRoot = FileManager.default.temporaryDirectory.resolvingSymlinksInPath()
	let requestRoot = parentURL.deletingLastPathComponent().resolvingSymlinksInPath()
	if requestRoot != temporaryRoot {
		throw MailerFailure.message("The mail request is outside the temporary directory.")
	}

	let requestStatus = try checkedStatus(for: requestURL.path, expectedType: S_IFREG)
	if (requestStatus.st_mode & 0o077) != 0 {
		throw MailerFailure.message("The mail request is not private.")
	}
	if requestStatus.st_size > maximumRequestBytes {
		throw MailerFailure.message("The mail request is too large.")
	}
}

private func loadRequest(from requestURL: URL) throws -> MailRequest {
	let requestData = try Data(contentsOf: requestURL, options: .mappedIfSafe)
	let request = try JSONDecoder().decode(MailRequest.self, from: requestData)
	return request
}

private func validateAttachment(_ attachmentPath: String?) throws -> String {
	guard let attachmentPath else {
		return ""
	}
	let attachmentURL = URL(fileURLWithPath: attachmentPath).standardizedFileURL
	if attachmentURL.pathExtension.lowercased() != "xlsx" {
		throw MailerFailure.message("The mail attachment must be an xlsx file.")
	}

	// The installed app lives at the repository root, so only generated output/
	// workbooks are valid attachments (ASVS 5.3.2 and 8.1.1).
	let repositoryRoot = Bundle.main.bundleURL.deletingLastPathComponent()
	let outputRoot = repositoryRoot.appendingPathComponent(
		"output",
		isDirectory: true
	).resolvingSymlinksInPath()
	let resolvedAttachment = attachmentURL.resolvingSymlinksInPath()
	if resolvedAttachment.deletingLastPathComponent() != outputRoot {
		throw MailerFailure.message("The mail attachment is outside the output directory.")
	}
	let attachmentStatus = try checkedStatus(
		for: attachmentURL.path,
		expectedType: S_IFREG
	)
	if attachmentStatus.st_size > maximumAttachmentBytes {
		throw MailerFailure.message("The mail attachment is too large.")
	}
	return resolvedAttachment.path
}

private func validateRequest(_ request: MailRequest) throws -> String {
	if request.version != requestVersion {
		throw MailerFailure.message("The mail request version is unsupported.")
	}
	let recipientSet = Set(request.recipients)
	if request.recipients.isEmpty || recipientSet.count != request.recipients.count {
		throw MailerFailure.message("Mail recipients must be nonempty and unique.")
	}
	if !recipientSet.isSubset(of: allowedRecipients) {
		throw MailerFailure.message("The mail request contains an unapproved recipient.")
	}
	if request.subject.isEmpty || request.subject.utf8.count > maximumSubjectBytes {
		throw MailerFailure.message("The mail subject is invalid.")
	}
	if request.subject.contains("\n") || request.subject.contains("\r") {
		throw MailerFailure.message("The mail subject contains a line break.")
	}
	if request.subject.contains("\0") || request.body.contains("\0") {
		throw MailerFailure.message("The mail request contains a null character.")
	}
	if request.body.utf8.count > maximumBodyBytes {
		throw MailerFailure.message("The mail body is too large.")
	}
	return try validateAttachment(request.attachmentPath)
}

private func appleScriptError(_ errorInfo: NSDictionary?) -> String {
	guard let errorInfo else {
		return "Mail.app automation failed."
	}
	let errorMessage = errorInfo["NSAppleScriptErrorMessage"] as? String
	let errorNumber = errorInfo["NSAppleScriptErrorNumber"] as? NSNumber
	if let errorMessage, let errorNumber {
		return "\(errorMessage) (\(errorNumber))"
	}
	return "Mail.app automation failed."
}

private func mailAutomationPermissionStatus(
	askUserIfNeeded: Bool
) throws -> OSStatus {
	let targetDescriptor = NSAppleEventDescriptor(bundleIdentifier: "com.apple.mail")
	guard let target = targetDescriptor.aeDesc else {
		throw MailerFailure.message("Mail.app could not be addressed for Automation.")
	}

	return AEDeterminePermissionToAutomateTarget(
		target,
		typeWildCard,
		typeWildCard,
		askUserIfNeeded
	)
}

private func sendMail(
	_ request: MailRequest,
	attachmentPath: String,
	permissionPromptHandler: () -> Void
) throws {
	// Check without UI first so already approved scheduled messages remain quiet.
	var permissionStatus = try mailAutomationPermissionStatus(askUserIfNeeded: false)
	if permissionStatus == errAEEventWouldRequireUserConsent {
		permissionPromptHandler()
		// This supported consent entry point runs away from the main thread
		// because the user's decision may take an arbitrary time.
		permissionStatus = try mailAutomationPermissionStatus(askUserIfNeeded: true)
	}
	if permissionStatus != noErr {
		throw MailerFailure.message(
			"CourseFinderMailer does not have Mail.app Automation permission (\(permissionStatus))."
		)
	}

	let script = OSAScript(source: mailScriptSource)
	var errorInfo: NSDictionary?

	// Typed handler arguments keep all dynamic content out of AppleScript source
	// and shell parsing (ASVS 1.2.5).
	let result = script.executeHandler(
		withName: "sendMessage",
		arguments: [request.recipients, request.subject, request.body, attachmentPath],
		error: &errorInfo
	)
	if result?.stringValue != "sent" {
		throw MailerFailure.message(appleScriptError(errorInfo))
	}
}

private func writeResult(_ result: MailResult, to resultURL: URL) throws {
	let resultData = try JSONEncoder().encode(result)
	try resultData.write(to: resultURL, options: .atomic)
	if chmod(resultURL.path, S_IRUSR | S_IWUSR) != 0 {
		unlink(resultURL.path)
		throw MailerFailure.message("The mail result permissions could not be secured.")
	}
}

private func processRequest(
	at requestURL: URL,
	permissionPromptHandler: () -> Void
) {
	// Do not create a result beside an untrusted caller-provided path. Validate
	// the private request directory before deriving any output (ASVS 5.3.2).
	do {
		try validateRequestLocation(requestURL)
	} catch {
		fputs("CourseFinderMailer rejected the request location.\n", stderr)
		return
	}
	let resultURL = URL(fileURLWithPath: "\(requestURL.path).result.json")
	let result: MailResult
	do {
		let request = try loadRequest(from: requestURL)
		let attachmentPath = try validateRequest(request)
		try sendMail(
			request,
			attachmentPath: attachmentPath,
			permissionPromptHandler: permissionPromptHandler
		)
		result = MailResult(status: "sent", error: nil)
	} catch {
		// Never return the subject or body in an error (ASVS 16.3.4 and 16.5.3).
		result = MailResult(status: "failed", error: String(describing: error))
	}
	do {
		try writeResult(result, to: resultURL)
	} catch {
		fputs("CourseFinderMailer could not write its result.\n", stderr)
	}
}

private final class MailerApplicationDelegate: NSObject, NSApplicationDelegate {
	private var statusWindow: NSWindow?

	func applicationDidFinishLaunching(_ notification: Notification) {
		guard CommandLine.arguments.count == 2 else {
			fputs("CourseFinderMailer requires one private request path.\n", stderr)
			NSApplication.shared.terminate(nil)
			return
		}

		let requestURL = URL(fileURLWithPath: CommandLine.arguments[1])
		do {
			try validateRequestLocation(requestURL)
		} catch {
			fputs("CourseFinderMailer rejected the request location.\n", stderr)
			NSApplication.shared.terminate(nil)
			return
		}

		launchMailAndProcess(requestURL)
	}

	private func launchMailAndProcess(_ requestURL: URL) {
		guard let mailURL = NSWorkspace.shared.urlForApplication(
			withBundleIdentifier: "com.apple.mail"
		) else {
			processAndFinish(requestURL)
			return
		}
		let configuration = NSWorkspace.OpenConfiguration()
		configuration.activates = false
		NSWorkspace.shared.openApplication(
			at: mailURL,
			configuration: configuration
		) { [weak self] _, _ in
			self?.processAndFinish(requestURL)
		}
	}

	private func processAndFinish(_ requestURL: URL) {
		// Keep the main AppKit run loop responsive while the system consent
		// dialog waits for a decision and while Mail handles the AppleEvent.
		DispatchQueue.global(qos: .userInitiated).async { [weak self] in
			processRequest(at: requestURL) {
				self?.showPermissionWindowFromBackground()
			}
			DispatchQueue.main.async {
				self?.statusWindow?.close()
				NSApplication.shared.terminate(nil)
			}
		}
	}

	private func showPermissionWindowFromBackground() {
		DispatchQueue.main.sync {
			NSApplication.shared.setActivationPolicy(.regular)
			showStatusWindow()
			NSApplication.shared.activate(ignoringOtherApps: true)
		}
		// Let AppKit render the status window before the background thread asks
		// TCC to display its system consent dialog.
		Thread.sleep(forTimeInterval: 0.75)
	}

	private func showStatusWindow() {
		let contentRect = NSRect(x: 0, y: 0, width: 460, height: 150)
		let window = NSWindow(
			contentRect: contentRect,
			styleMask: [.titled],
			backing: .buffered,
			defer: false
		)
		window.title = "Course Finder Mailer"
		window.isReleasedWhenClosed = false
		window.level = .floating
		window.center()

		let message = NSTextField(
			wrappingLabelWithString: "Waiting for macOS to allow CourseFinderMailer to control Mail.app.\n\nClick Allow in the system prompt."
		)
		message.alignment = .center
		message.font = NSFont.systemFont(ofSize: 15)
		message.translatesAutoresizingMaskIntoConstraints = false

		let contentView = NSView(frame: contentRect)
		contentView.addSubview(message)
		NSLayoutConstraint.activate([
			message.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 30),
			message.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -30),
			message.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
		])
		window.contentView = contentView
		window.makeKeyAndOrderFront(nil)
		statusWindow = window
	}
}

private let application = NSApplication.shared
private let applicationDelegate = MailerApplicationDelegate()
application.delegate = applicationDelegate
application.setActivationPolicy(.accessory)
application.run()
