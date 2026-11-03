// SPDX-License-Identifier: Apache-2.0
import Foundation
import XCTest

/// Independent, public XCTest input only. Never launches/relaunches the library
/// app, calls a Kotlin manager/delegate, or touches a different bundle.
final class NativeCmpKitInputTests: XCTestCase {
    private var endpoint: URL!
    private var token = ""
    private var application: XCUIApplication!
    private var session: URLSession!

    override func setUpWithError() throws {
        startup("setup-enter")
        do { try configureInput(); startup("setup-configured") }
        catch { startup("setup-refused"); throw error }
    }

    private func configureInput() throws {
        continueAfterFailure = false
        let environment = ProcessInfo.processInfo.environment
        token = try required(environment["NATIVECMPKIT_INPUT_AUTH"])
        let sessionToken = try required(environment["NATIVECMPKIT_INPUT_SESSION"])
        let url = try required(environment["NATIVECMPKIT_INPUT_URL"])
        let bundle = try required(environment["NATIVECMPKIT_INPUT_BUNDLE"])
        guard token.range(of: "^[0-9a-f]{32}$", options: .regularExpression) != nil,
              sessionToken.range(of: "^[0-9a-f]{32}$", options: .regularExpression) != nil, token != sessionToken,
              let parsed = URL(string: url), parsed.scheme == "http",
              parsed.host == "127.0.0.1", let port = parsed.port, (1...65535).contains(port),
              parsed.path.isEmpty || parsed.path == "/",
              parsed.user == nil, parsed.password == nil, parsed.query == nil, parsed.fragment == nil,
              bundle.range(of: "^io\\.github\\.apdelrahman1911\\.nativecmpkit\\.verification\\.ui\\.r[0-9a-f]{12}\\.t[0-9a-f]{32}$", options: .regularExpression) != nil,
              bundle.hasSuffix(".t" + sessionToken) else { throw InputError.invalidConfiguration }
        endpoint = parsed
        application = XCUIApplication(bundleIdentifier: bundle)
        let configuration = URLSessionConfiguration.ephemeral
        configuration.timeoutIntervalForRequest = 5
        configuration.timeoutIntervalForResource = 5
        configuration.httpCookieStorage = nil
        configuration.urlCache = nil
        session = URLSession(configuration: configuration)
    }

    override func tearDownWithError() throws {
        session?.invalidateAndCancel()
    }

    func testDeliverOnlyOwnedLibraryNativeInput() throws {
        startup("ready-enter")
        _ = try exchange("ready", body: [:])
        startup("ready-acknowledged")
        let deadline = ProcessInfo.processInfo.systemUptime + 900
        var previous = 0
        while ProcessInfo.processInfo.systemUptime < deadline {
            guard let request = try exchange("next") else {
                Thread.sleep(forTimeInterval: 0.05)
                continue
            }
            if request["operation"] as? String == "finish" {
                _ = try exchange("finished", body: ["delivered": previous])
                startup("finished")
                return
            }
            let sequence = try number(request["sequence"])
            guard sequence == previous + 1 && sequence <= 96 else { throw InputError.sequence }
            do {
                var response = try deliver(request)
                response["sequence"] = sequence
                response["status"] = "delivered"
                _ = try exchange("response", body: response)
                previous = sequence
            } catch {
                // Fixed failure only: do not serialize configuration, paths,
                // arbitrary exception bodies, authentication or screenshots.
                let reason = (error as? InputError).map { String(describing: $0) } ?? "transport"
                _ = try exchange("response", body: ["sequence": sequence, "status": "refused", "reason": reason])
                throw error
            }
        }
        throw InputError.deadline
    }

    private func deliver(_ request: [String: Any]) throws -> [String: Any] {
        guard application.state == .runningForeground else { throw InputError.foreignOrInactiveApplication }
        let operation = try required(request["operation"] as? String)
        switch operation {
        case "alert-button", "alert-field":
            let title = try required(request["title"] as? String)
            let label = try required(request["label"] as? String)
            let alert = application.alerts.element(boundBy: 0)
            guard alert.waitForExistence(timeout: 5), application.alerts.count == 1,
                  alert.staticTexts.matching(identifier: title).count == 1 else { throw InputError.notUnique }
            if operation == "alert-button" {
                let query = alert.buttons.matching(identifier: label)
                let button = query.element(boundBy: 0)
                guard button.waitForExistence(timeout: 5), query.count == 1,
                      button.isEnabled, button.isHittable else { throw InputError.notHittable }
                button.tap()
                return ["operation": operation, "unique": true, "enabled": true, "hittable": true]
            }
            let query = alert.textFields.matching(identifier: label)
            let field = query.element(boundBy: 0)
            let text = try required(request["text"] as? String)
            guard text.count <= 128, field.waitForExistence(timeout: 5), query.count == 1,
                  field.isEnabled, field.isHittable else { throw InputError.notHittable }
            field.tap()
            field.typeText(text)
            return ["operation": operation, "unique": true, "value": field.value as? String ?? ""]
        case "tap", "drag":
            let from = try coordinate(request, x: "x", y: "y")
            if operation == "tap" { from.tap() }
            else {
                let to = try coordinate(request, x: "toX", y: "toY")
                from.press(forDuration: 0.1, thenDragTo: to, withVelocity: .slow, thenHoldForDuration: 0.2)
            }
            return ["operation": operation, "foreground": true]
        default: throw InputError.unknownOperation
        }
    }

    private func coordinate(_ request: [String: Any], x: String, y: String) throws -> XCUICoordinate {
        guard let px = request[x] as? Double, let py = request[y] as? Double,
              px.isFinite, py.isFinite, (0.01...0.99).contains(px), (0.01...0.99).contains(py),
              application.frame.width > 0, application.frame.height > 0 else { throw InputError.coordinate }
        return application.coordinate(withNormalizedOffset: CGVector(dx: px, dy: py))
    }

    private func exchange(_ path: String, body: [String: Any]? = nil) throws -> [String: Any]? {
        var request = URLRequest(url: endpoint.appendingPathComponent(path))
        request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")
        request.httpMethod = body == nil ? "GET" : "POST"
        if let body = body {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        let completed = DispatchSemaphore(value: 0)
        var result: Result<[String: Any]?, Error>?
        session.dataTask(with: request) { data, response, error in
            defer { completed.signal() }
            do {
                if let error = error {
                    let failure = error as NSError
                    let known = ["NSURLErrorDomain", "NSCocoaErrorDomain", "NSPOSIXErrorDomain"]
                    let domain = known.contains(failure.domain) ? failure.domain : "other"
                    if (-2147483648...2147483647).contains(failure.code) {
                        print("NATIVECMPKIT_XCTEST_TRANSPORT domain=\(domain) code=\(failure.code)")
                    }
                    throw error
                }
                guard let response = response as? HTTPURLResponse else { throw InputError.transport }
                if response.statusCode == 204 { result = .success(nil); return }
                guard response.statusCode == 200, let data = data, data.count <= 8192,
                      let object = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                    throw InputError.transport
                }
                result = .success(object)
            } catch { result = .failure(error) }
        }.resume()
        guard completed.wait(timeout: .now() + 6) == .success, let result = result else {
            throw InputError.transport
        }
        return try result.get()
    }

    private func startup(_ phase: String) {
        // Call sites supply fixed literals, never environment/error contents.
        print("NATIVECMPKIT_XCTEST_STARTUP \(phase)")
    }

    private func required(_ value: String?) throws -> String {
        guard let value = value, !value.isEmpty, value.count <= 256 else { throw InputError.invalidConfiguration }
        return value
    }

    private func number(_ value: Any?) throws -> Int {
        guard let number = value as? Int else { throw InputError.sequence }
        return number
    }

    private enum InputError: Error {
        case invalidConfiguration, sequence, deadline, foreignOrInactiveApplication
        case notUnique, notHittable, coordinate, unknownOperation, transport
    }
}
