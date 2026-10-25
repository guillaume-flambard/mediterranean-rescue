import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, errorCode, resetCsrfToken } from "../api/client";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { Link, navigate } from "../router";
import { Button } from "../ui/Button";
import { InlineMessage, PendingState } from "../ui/Feedback";
import { AccountFrame } from "./AccountFrame";

type Key = Parameters<I18n["t"]>[0];

/** The token travels after "#": the browser never sends it to a server, so no log ever holds it. */
function tokenFromAddress() {
  return window.location.hash.slice(1);
}

// Landing page of an invitation link (ADR 0015). Opening it only reads the invitation; joining is
// the button, so a mail scanner that follows links uses nothing up.
export function InvitationPage() {
  const i18n = useI18n();
  const { t } = i18n;
  const queryClient = useQueryClient();
  const [token] = useState(tokenFromAddress);
  const offer = api.useQuery(
    "post",
    "/api/private/v1/invitations/check/",
    { body: { token } },
    { enabled: token.length > 0, retry: false, refetchOnWindowFocus: false },
  );
  const accept = api.useMutation("post", "/api/private/v1/invitations/accept/");
  const [failed, setFailed] = useState(false);

  const join = async () => {
    setFailed(false);
    try {
      await accept.mutateAsync({ body: { token } });
      resetCsrfToken();
      // The link is spent: it leaves the address and the history entry.
      window.history.replaceState(null, "", "/invite");
      await queryClient.invalidateQueries();
      navigate("/workspace");
    } catch {
      setFailed(true);
    }
  };

  const unusable = !token || offer.error || (failed && errorCode(accept.error) === "invitation_unusable");
  return (
    <AccountFrame titleId="invite-title">
      <div className="sign-in">
        {offer.isPending && token ? (
          <PendingState label={t("invite.loading")} />
        ) : unusable ? (
          <>
            <h1 id="invite-title">{t("invite.unusableTitle")}</h1>
            <p className="sign-in__lead">{t("invite.unusable")}</p>
            <Link to="/workspace" className="account__back">
              {t("invite.toSignIn")}
            </Link>
          </>
        ) : offer.data ? (
          <>
            <h1 id="invite-title">{t("invite.title")}</h1>
            <p className="sign-in__lead">{t("invite.lead", { name: offer.data.invited_by })}</p>
            {offer.data.roles.length > 0 && (
              <div className="invite__roles">
                <p>{t("invite.roles")}</p>
                <ul>
                  {offer.data.roles.map((role) => (
                    <li key={role}>{t(`role.${role}` as Key)}</li>
                  ))}
                </ul>
              </div>
            )}
            {failed && <InlineMessage tone="error">{t("invite.failed")}</InlineMessage>}
            <Button variant="primary" size="lg" loading={accept.isPending} onClick={() => void join()}>
              {t("invite.join")}
            </Button>
            <p className="sign-in__privacy">
              {t("invite.once", { date: i18n.date(offer.data.expires_at.slice(0, 10)) })}
            </p>
          </>
        ) : null}
      </div>
    </AccountFrame>
  );
}
