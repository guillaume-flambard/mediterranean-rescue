import { useI18n } from "../i18n/I18nProvider";
import { InlineMessage } from "../ui/Feedback";
import { SignIn } from "./SignIn";

// 401 asks to sign in (the Django session login), 403 says the permission is missing; neither is
// shown as an empty result.
export function AccessProblem({ code }: { code: "not_authenticated" | "permission_denied" }) {
  const { t } = useI18n();
  if (code === "permission_denied") return <InlineMessage tone="warning">{t("review.access.denied")}</InlineMessage>;
  return <SignIn />;
}
