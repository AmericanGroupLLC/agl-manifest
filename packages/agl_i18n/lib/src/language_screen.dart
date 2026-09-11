import 'package:flutter/material.dart';

import '../l10n/generated/agl_localizations.dart';
import 'agl_locales.dart';
import 'locale_controller.dart';

/// The language picker every app uses.
///
/// Its own labels come from this package's catalogue, so the picker is itself
/// translated — a language screen that only speaks English is no use to the
/// person who needs it.
class AglLanguageScreen extends StatelessWidget {
  const AglLanguageScreen({super.key, required this.controller});

  final AglLocaleController controller;

  @override
  Widget build(BuildContext context) {
    final agl = AglL10n.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(agl?.miscLanguage ?? 'Language')),
      body: AglLanguageList(controller: controller),
    );
  }
}

/// The list on its own, for apps that show language inside an existing
/// settings page rather than pushing a screen.
class AglLanguageList extends StatelessWidget {
  const AglLanguageList({super.key, required this.controller});

  final AglLocaleController controller;

  @override
  Widget build(BuildContext context) {
    final agl = AglL10n.of(context);
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) => ListView(
        children: [
          RadioListTile<Locale?>(
            value: null,
            groupValue: controller.locale,
            onChanged: controller.setLocale,
            title: Text(agl?.miscSystemDefault ?? 'System default'),
            subtitle: Text(
                agl?.miscFollowDeviceLanguage ?? 'Follow the device language'),
          ),
          const Divider(height: 1),
          for (final locale in controller.supportedLocales)
            RadioListTile<Locale?>(
              value: locale,
              groupValue: controller.locale,
              onChanged: controller.setLocale,
              // Each row is laid out in its own script's direction, so Arabic
              // reads correctly even while the app is still in English.
              title: Directionality(
                textDirection: AglLocales.isRtl(locale.languageCode)
                    ? TextDirection.rtl
                    : TextDirection.ltr,
                child: Text(AglLocales.nativeName(locale.languageCode)),
              ),
            ),
        ],
      ),
    );
  }
}
