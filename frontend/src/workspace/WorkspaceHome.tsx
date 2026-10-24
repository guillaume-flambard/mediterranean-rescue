import { useEffect } from "react";
import { api, errorCode } from "../api/client";
import { useI18n } from "../i18n/I18nProvider";
import { AccessProblem } from "../review/AccessProblem";
import { navigate } from "../router";
import { InlineMessage, PendingState } from "../ui/Feedback";
import { homeSection } from "./WorkspaceShell";

// W01: /workspace opens the first section this user may use.
export function WorkspaceHome() {
  const { t } = useI18n();
  const me = api.useQuery("get", "/api/private/v1/me/", {});
  const target = me.data ? homeSection(me.data) : null;
  useEffect(() => {
    if (target) navigate(target, { replace: true });
  }, [target]);
  if (me.error) {
    const code = errorCode(me.error);
    if (code === "not_authenticated" || code === "permission_denied") return <AccessProblem code={code} />;
    return <InlineMessage tone="error">{t("workspace.loadError")}</InlineMessage>;
  }
  if (me.data && !target) {
    return (
      <main className="review">
        <AccessProblem code="permission_denied" />
      </main>
    );
  }
  return <PendingState label={t("workspace.loading")} />;
}
