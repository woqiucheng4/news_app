class AppConstants {
  const AppConstants._();

  static const String apiBaseUrl = String.fromEnvironment(
    'NEWSFLOW_API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );
  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 20);
  static const String analyticsAdapter = String.fromEnvironment(
    'NEWSFLOW_ANALYTICS_ADAPTER',
    defaultValue: 'debug',
  );
  static const String analyticsTransport = String.fromEnvironment(
    'NEWSFLOW_ANALYTICS_TRANSPORT',
    defaultValue: 'debug',
  );
  static const String analyticsEndpoint = String.fromEnvironment(
    'NEWSFLOW_ANALYTICS_ENDPOINT',
    defaultValue: '',
  );
  static const bool analyticsRedactSearch = bool.fromEnvironment(
    'NEWSFLOW_ANALYTICS_REDACT_SEARCH',
  );
  static const String googleWebClientId = String.fromEnvironment(
    'NEWSFLOW_GOOGLE_WEB_CLIENT_ID',
    defaultValue: '',
  );
  static const String googleIosClientId = String.fromEnvironment(
    'NEWSFLOW_GOOGLE_IOS_CLIENT_ID',
    defaultValue: '',
  );
  static const String privacyPolicyUrl = String.fromEnvironment(
    'NEWSFLOW_PRIVACY_POLICY_URL',
    defaultValue: 'https://github.com/woqiucheng4/news_app/blob/main/docs/PRIVACY_POLICY.md',
  );
}
