Hello,

Thank you for your message. WiFiTrail does not have VPN features. The details are below, and we have added the same text to the App Review Information section in App Store Connect.

VPN FUNCTIONALITY
WiFiTrail has no VPN features. It does not create, configure, start or route traffic through any VPN. It contains no Network Extension (no packet tunnel, app proxy, content filter or DNS proxy provider), it does not use NEVPNManager or NETunnelProviderManager, and it has no Network Extension or VPN entitlement. The only networking capability it declares is Access Wi-Fi Information.

Why the automated analysis flagged it: the open-source Flutter plugin network_info_plus links NetworkExtension.framework for one call, NEHotspotNetwork fetchCurrent. That call returns the name (SSID) and BSSID of the Wi-Fi network the device is already connected to, and the Connection screen shows them to the user. "VPN" also appears in the app's text in two places. The first is a connection-type label, shown only when the operating system itself reports a VPN transport. That happens on Android only. On iOS the app reads NWPathMonitor, which has no VPN category, so the label never appears. The second is a fixed security tip that tells users to use a VPN of their own choosing on public networks. The app does not detect, provide, recommend, link to or sell any VPN service.

1. What user information is the app collecting using VPN?
None. The app has no VPN. The Wi-Fi name and BSSID described above are read on the device and shown on screen only. They are not stored, logged or sent anywhere.

2. For what purposes is the app collecting this information?
None. No information is collected through a VPN. The Wi-Fi name is shown only so the user can confirm which network they are looking at and testing.

3. Will the data be shared with any third parties?
No. Nothing is collected through a VPN, so nothing is shared. The app makes only two kinds of network traffic. One is the speed test the user starts, which sends and receives test bytes to and from speed.cloudflare.com. The other is Firebase Crashlytics crash reporting, along with the Firebase (Google) services it depends on. The app never puts the Wi-Fi name, the BSSID or the device's local addresses into either one.

Thank you.
