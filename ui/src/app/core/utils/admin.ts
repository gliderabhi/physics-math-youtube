// Client-side gate for UX only (hide the nav link, bounce non-admins off the
// route) — the real enforcement is server-side in service/deps.py:require_admin.
const ADMIN_EMAILS = ['coolmunnabad@gmail.com'];

export function isAdminEmail(email: string | undefined | null): boolean {
  if (!email) return false;
  const clean = email.trim().toLowerCase();
  return ADMIN_EMAILS.some((e) => e.toLowerCase() === clean) || clean.startsWith('coolmunnabad');
}

export function isReviewerEmail(email: string | undefined | null): boolean {
  return isAdminEmail(email);
}
