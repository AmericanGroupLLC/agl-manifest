import Flutter
import UIKit
import UserNotifications

// Repro probe for the iOS 27 flutter_local_notifications cancel hang.
// - A watchdog thread logs whenever the main thread stops answering.
// - The "fln_probe" channel calls single UNUserNotificationCenter APIs directly
//   (bypassing the plugin), on the main thread or on a background queue.
func plog(_ s: String) {
  let t = String(format: "%.3f", Date().timeIntervalSince1970)
  NSLog("FLNPROBE %@ %@", t, s)
}

final class MainWatchdog {
  static var lastTick = Date()
  static let lock = NSLock()
  static func start() {
    let th = Thread {
      var reported = 0
      while true {
        Thread.sleep(forTimeInterval: 0.5)
        DispatchQueue.main.async {
          lock.lock(); lastTick = Date(); lock.unlock()
        }
        lock.lock(); let gap = Date().timeIntervalSince(lastTick); lock.unlock()
        if gap > 2.0 {
          let secs = Int(gap)
          if secs != reported { reported = secs; plog("WATCHDOG main thread stalled \(secs)s") }
        } else if reported != 0 {
          plog("WATCHDOG main thread recovered after \(reported)s"); reported = 0
        }
      }
    }
    th.name = "fln-watchdog"
    th.start()
  }
}

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    plog("didFinishLaunching args=\(ProcessInfo.processInfo.arguments) os=\(UIDevice.current.systemVersion)")
    MainWatchdog.start()
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
    let reg = engineBridge.pluginRegistry.registrar(forPlugin: "FlnProbe")!
    let ch = FlutterMethodChannel(name: "fln_probe", binaryMessenger: reg.messenger())
    ch.setMethodCallHandler { call, result in
      switch call.method {
      case "args":
        result(ProcessInfo.processInfo.arguments)
      case "log":
        plog("DART \(call.arguments as? String ?? "")")
        result(nil)
      case "native":
        let a = call.arguments as! [String: Any]
        AppDelegate.runNative(api: a["api"] as! String, bg: a["bg"] as? Bool ?? false, result: result)
      default:
        result(FlutterMethodNotImplemented)
      }
    }
  }

  static func runNative(api: String, bg: Bool, result: @escaping FlutterResult) {
    let c = UNUserNotificationCenter.current()
    let ids = ["1001"]
    let work: () -> Void = {
      let t0 = Date()
      plog("NATIVE \(api) bg=\(bg) start thread=\(Thread.isMainThread ? "main" : "bg")")
      switch api {
      case "removePending": c.removePendingNotificationRequests(withIdentifiers: ids)
      case "removeDelivered": c.removeDeliveredNotifications(withIdentifiers: ids)
      case "removeAllPending": c.removeAllPendingNotificationRequests()
      case "removeAllDelivered": c.removeAllDeliveredNotifications()
      default: break
      }
      let ms = Int(Date().timeIntervalSince(t0) * 1000)
      plog("NATIVE \(api) bg=\(bg) returned after \(ms)ms")
      DispatchQueue.main.async { result(ms) }
    }
    switch api {
    case "getPending":
      plog("NATIVE getPending start")
      c.getPendingNotificationRequests { r in
        plog("NATIVE getPending -> \(r.map { $0.identifier })")
        DispatchQueue.main.async { result(r.map { $0.identifier }) }
      }
    case "getDelivered":
      plog("NATIVE getDelivered start")
      c.getDeliveredNotifications { r in
        plog("NATIVE getDelivered -> \(r.map { $0.request.identifier })")
        DispatchQueue.main.async { result(r.map { $0.request.identifier }) }
      }
    case "auth":
      c.getNotificationSettings { s in
        plog("NATIVE auth status=\(s.authorizationStatus.rawValue)")
        DispatchQueue.main.async { result(s.authorizationStatus.rawValue) }
      }
    default:
      if bg { DispatchQueue.global(qos: .userInitiated).async(execute: work) } else { work() }
    }
  }
}
