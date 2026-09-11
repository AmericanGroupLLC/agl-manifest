import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'agl_localizations_ar.dart';
import 'agl_localizations_de.dart';
import 'agl_localizations_en.dart';
import 'agl_localizations_es.dart';
import 'agl_localizations_fr.dart';
import 'agl_localizations_hi.dart';
import 'agl_localizations_it.dart';
import 'agl_localizations_ja.dart';
import 'agl_localizations_ko.dart';
import 'agl_localizations_pt.dart';
import 'agl_localizations_ru.dart';
import 'agl_localizations_zh.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AglL10n
/// returned by `AglL10n.of(context)`.
///
/// Applications need to include `AglL10n.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/agl_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AglL10n.localizationsDelegates,
///   supportedLocales: AglL10n.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AglL10n.supportedLocales
/// property.
abstract class AglL10n {
  AglL10n(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AglL10n? of(BuildContext context) {
    return Localizations.of<AglL10n>(context, AglL10n);
  }

  static const LocalizationsDelegate<AglL10n> delegate = _AglL10nDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('ar'),
    Locale('de'),
    Locale('en'),
    Locale('es'),
    Locale('fr'),
    Locale('hi'),
    Locale('it'),
    Locale('ja'),
    Locale('ko'),
    Locale('pt'),
    Locale('ru'),
    Locale('zh')
  ];

  /// Button: commit a change.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get actionSave;

  /// Button: abandon a dialog or flow.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get actionCancel;

  /// Button: destroy something permanently.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get actionDelete;

  /// Button: take out of a list, not destroy.
  ///
  /// In en, this message translates to:
  /// **'Remove'**
  String get actionRemove;

  /// Button: create or attach a new item.
  ///
  /// In en, this message translates to:
  /// **'Add'**
  String get actionAdd;

  /// Button: open something for changes.
  ///
  /// In en, this message translates to:
  /// **'Edit'**
  String get actionEdit;

  /// Button shown after a failure.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get actionRetry;

  /// Button: dismiss a sheet or dialog.
  ///
  /// In en, this message translates to:
  /// **'Close'**
  String get actionClose;

  /// Button: return to the previous screen.
  ///
  /// In en, this message translates to:
  /// **'Back'**
  String get actionBack;

  /// Button: proceed in a multi-step flow.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get actionContinue;

  /// Button: advance one step.
  ///
  /// In en, this message translates to:
  /// **'Next'**
  String get actionNext;

  /// Button: bypass an optional step.
  ///
  /// In en, this message translates to:
  /// **'Skip'**
  String get actionSkip;

  /// Button: finish and leave.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get actionDone;

  /// Button: return to defaults.
  ///
  /// In en, this message translates to:
  /// **'Reset'**
  String get actionReset;

  /// Button: open the system share sheet.
  ///
  /// In en, this message translates to:
  /// **'Share'**
  String get actionShare;

  /// Button or field label for searching.
  ///
  /// In en, this message translates to:
  /// **'Search'**
  String get actionSearch;

  /// Button: empty a field.
  ///
  /// In en, this message translates to:
  /// **'Clear'**
  String get actionClear;

  /// Button: empty every filter or entry at once.
  ///
  /// In en, this message translates to:
  /// **'Clear all'**
  String get actionClearAll;

  /// Accessible label on the X inside a search field.
  ///
  /// In en, this message translates to:
  /// **'Clear search'**
  String get actionClearSearch;

  /// Link at the end of a preview row.
  ///
  /// In en, this message translates to:
  /// **'See all'**
  String get actionSeeAll;

  /// Button: fetch again.
  ///
  /// In en, this message translates to:
  /// **'Refresh'**
  String get actionRefresh;

  /// Button: commit filter choices.
  ///
  /// In en, this message translates to:
  /// **'Apply'**
  String get actionApply;

  /// Button: agree to a consequential action.
  ///
  /// In en, this message translates to:
  /// **'Confirm'**
  String get actionConfirm;

  /// Button: begin a timed or recorded activity.
  ///
  /// In en, this message translates to:
  /// **'Start'**
  String get actionStart;

  /// Button: end a timed or recorded activity.
  ///
  /// In en, this message translates to:
  /// **'Stop'**
  String get actionStop;

  /// Bottom navigation tab.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// Bottom navigation tab.
  ///
  /// In en, this message translates to:
  /// **'Search'**
  String get navSearch;

  /// Bottom navigation tab.
  ///
  /// In en, this message translates to:
  /// **'Saved'**
  String get navSaved;

  /// Bottom navigation tab.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get navProfile;

  /// Bottom navigation tab or menu entry.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get navSettings;

  /// Bottom navigation tab for exploring a catalogue.
  ///
  /// In en, this message translates to:
  /// **'Browse'**
  String get navBrowse;

  /// Bottom navigation tab for recent events.
  ///
  /// In en, this message translates to:
  /// **'Activity'**
  String get navActivity;

  /// Settings section for the signed-in user.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get navAccount;

  /// Settings section or screen title.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get navNotifications;

  /// Button and screen title.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get authSignIn;

  /// Destructive-ish menu entry.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get authSignOut;

  /// Button: register a new account.
  ///
  /// In en, this message translates to:
  /// **'Create account'**
  String get authSignUp;

  /// Text field label.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get authEmail;

  /// Text field label.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get authPassword;

  /// OAuth button. "Google" is a brand and stays.
  ///
  /// In en, this message translates to:
  /// **'Continue with Google'**
  String get authContinueWithGoogle;

  /// OAuth button. "Apple" is a brand and stays.
  ///
  /// In en, this message translates to:
  /// **'Continue with Apple'**
  String get authContinueWithApple;

  /// Button: use the app without an account.
  ///
  /// In en, this message translates to:
  /// **'Continue as guest'**
  String get authContinueAsGuest;

  /// Text field label.
  ///
  /// In en, this message translates to:
  /// **'Name'**
  String get authName;

  /// Shown while waiting. Ends with an ellipsis.
  ///
  /// In en, this message translates to:
  /// **'Loading…'**
  String get stateLoading;

  /// Empty state on a saved/bookmarks screen.
  ///
  /// In en, this message translates to:
  /// **'Nothing saved yet'**
  String get stateNothingSaved;

  /// Empty state after a search.
  ///
  /// In en, this message translates to:
  /// **'No results'**
  String get stateNoResults;

  /// Generic error heading.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong'**
  String get stateSomethingWentWrong;

  /// Shown when the device has no connection.
  ///
  /// In en, this message translates to:
  /// **'You\'re offline'**
  String get stateOffline;

  /// Advice under an offline or network error.
  ///
  /// In en, this message translates to:
  /// **'Check your connection and try again'**
  String get stateCheckConnection;

  /// Settings entry and title of the language picker.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get miscLanguage;

  /// Language picker option: follow the device.
  ///
  /// In en, this message translates to:
  /// **'System default'**
  String get miscSystemDefault;

  /// Explanation under the system-default option.
  ///
  /// In en, this message translates to:
  /// **'Follow the device language'**
  String get miscFollowDeviceLanguage;

  /// Settings toggle.
  ///
  /// In en, this message translates to:
  /// **'Dark mode'**
  String get miscDarkMode;

  /// Settings link.
  ///
  /// In en, this message translates to:
  /// **'Privacy policy'**
  String get miscPrivacyPolicy;

  /// Settings link.
  ///
  /// In en, this message translates to:
  /// **'Terms of service'**
  String get miscTermsOfService;

  /// Settings section.
  ///
  /// In en, this message translates to:
  /// **'About'**
  String get miscAbout;

  /// Settings row showing the build version.
  ///
  /// In en, this message translates to:
  /// **'Version'**
  String get miscVersion;

  /// Title of a filter sheet.
  ///
  /// In en, this message translates to:
  /// **'Filters'**
  String get miscFilters;

  /// Button that opens sort options.
  ///
  /// In en, this message translates to:
  /// **'Sort'**
  String get miscSort;

  /// Relative date.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get miscToday;

  /// Relative date.
  ///
  /// In en, this message translates to:
  /// **'Yesterday'**
  String get miscYesterday;

  /// Label before a summed figure.
  ///
  /// In en, this message translates to:
  /// **'Total'**
  String get miscTotal;

  /// Filter option meaning no restriction.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get miscAll;

  /// Filter option meaning no preference.
  ///
  /// In en, this message translates to:
  /// **'Any'**
  String get miscAny;

  /// Section heading on a home screen.
  ///
  /// In en, this message translates to:
  /// **'Quick actions'**
  String get miscQuickActions;

  /// Disclaimer shown wherever demonstration data appears.
  ///
  /// In en, this message translates to:
  /// **'Sample data — not a live feed'**
  String get miscSampleData;
}

class _AglL10nDelegate extends LocalizationsDelegate<AglL10n> {
  const _AglL10nDelegate();

  @override
  Future<AglL10n> load(Locale locale) {
    return SynchronousFuture<AglL10n>(lookupAglL10n(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>[
        'ar',
        'de',
        'en',
        'es',
        'fr',
        'hi',
        'it',
        'ja',
        'ko',
        'pt',
        'ru',
        'zh'
      ].contains(locale.languageCode);

  @override
  bool shouldReload(_AglL10nDelegate old) => false;
}

AglL10n lookupAglL10n(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AglL10nAr();
    case 'de':
      return AglL10nDe();
    case 'en':
      return AglL10nEn();
    case 'es':
      return AglL10nEs();
    case 'fr':
      return AglL10nFr();
    case 'hi':
      return AglL10nHi();
    case 'it':
      return AglL10nIt();
    case 'ja':
      return AglL10nJa();
    case 'ko':
      return AglL10nKo();
    case 'pt':
      return AglL10nPt();
    case 'ru':
      return AglL10nRu();
    case 'zh':
      return AglL10nZh();
  }

  throw FlutterError(
      'AglL10n.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
