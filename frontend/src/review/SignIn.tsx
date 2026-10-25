import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, errorCode, resetCsrfToken } from "../api/client";
import { useI18n } from "../i18n/I18nProvider";
import { Button } from "../ui/Button";
import { InlineMessage } from "../ui/Feedback";
import { TextField } from "../ui/TextField";

// The application's own sign-in screen over the Django session (ADR 0009).
export function SignIn() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const signIn = api.useMutation("post", "/api/private/v1/session/");
  // On a local machine, a sign-out stops the automatic sign-in for this browser; it comes back here.
  const state = api.useQuery("get", "/api/private/v1/session/", {});
  const resume = api.useMutation("put", "/api/private/v1/session/");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [failure, setFailure] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const submit = async () => {
    setSubmitted(true);
    setFailure(null);
    if (!username.trim() || !password) return;
    try {
      await signIn.mutateAsync({ body: { username: username.trim(), password } });
      resetCsrfToken();
      setPassword("");
      await queryClient.invalidateQueries();
    } catch (error) {
      const code = errorCode(error);
      setFailure(
        code === "invalid_credentials"
          ? t("signIn.invalid")
          : code === "throttled"
            ? t("signIn.throttled")
            : t("signIn.failed"),
      );
    }
  };

  return (
    <div className="sign-in">
      <form
        className="sign-in__card"
        noValidate
        aria-labelledby="sign-in-title"
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <p className="sign-in__brand">{t("app.brand")}</p>
        <h1 id="sign-in-title">{t("signIn.title")}</h1>
        <p className="review-note">{t("signIn.lead")}</p>
        {failure && <InlineMessage tone="error">{failure}</InlineMessage>}
        {state.data?.local_auto_login && (
          <div className="sign-in__local">
            <p className="review-note">{t("signIn.localLead")}</p>
            <Button
              size="lg"
              loading={resume.isPending}
              onClick={async () => {
                setFailure(null);
                try {
                  await resume.mutateAsync({});
                  resetCsrfToken();
                  await queryClient.invalidateQueries();
                } catch {
                  setFailure(t("signIn.failed"));
                }
              }}
            >
              {t("signIn.localResume")}
            </Button>
          </div>
        )}
        <TextField
          label={t("signIn.username")}
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          error={submitted && !username.trim() ? t("signIn.usernameMissing") : null}
        />
        <TextField
          label={t("signIn.password")}
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={submitted && !password ? t("signIn.passwordMissing") : null}
        />
        <Button type="submit" variant="primary" size="lg" loading={signIn.isPending}>
          {t("signIn.submit")}
        </Button>
        <p className="review-note">{t("signIn.privacy")}</p>
      </form>
    </div>
  );
}
