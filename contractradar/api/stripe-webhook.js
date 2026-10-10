// BidBeacon — Stripe webhook (Vercel Node function).
// Flips a subscriber to 'active' on payment and 'canceled' when the subscription
// ends, in Supabase. The signup form (site/join.html) has already saved their
// profile as 'pending'; this closes the loop so digests start/stop automatically.
//
// Env (set in Vercel project settings):
//   STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, SUPABASE_URL, SUPABASE_SERVICE_KEY
// Point your Stripe webhook at https://bidbeacon.co.uk/api/stripe-webhook for
// events: checkout.session.completed, customer.subscription.deleted, invoice.paid.

const Stripe = require("stripe");
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || "");

function rawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", c => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function emailFrom(obj) {
  return (obj && (obj.customer_email ||
    (obj.customer_details && obj.customer_details.email) ||
    obj.email)) || null;
}

async function setStatus(email, status) {
  const base = process.env.SUPABASE_URL, key = process.env.SUPABASE_SERVICE_KEY;
  if (!base || !key || !email) return;
  await fetch(`${base}/rest/v1/subscribers?email=eq.${encodeURIComponent(email)}`, {
    method: "PATCH",
    headers: { apikey: key, Authorization: `Bearer ${key}`,
               "Content-Type": "application/json", Prefer: "return=minimal" },
    body: JSON.stringify({ status }),
  });
}

module.exports = async (req, res) => {
  if (req.method !== "POST") { res.status(405).end("Method Not Allowed"); return; }
  let event;
  try {
    const buf = await rawBody(req);
    event = stripe.webhooks.constructEvent(
      buf, req.headers["stripe-signature"], process.env.STRIPE_WEBHOOK_SECRET);
  } catch (e) {
    res.status(400).send(`Webhook signature verification failed: ${e.message}`);
    return;
  }

  try {
    const obj = event.data && event.data.object;
    if (event.type === "checkout.session.completed" || event.type === "invoice.paid") {
      await setStatus(emailFrom(obj), "active");
    } else if (event.type === "customer.subscription.deleted") {
      // subscription objects don't carry an email; resolve via the customer
      let email = emailFrom(obj);
      if (!email && obj && obj.customer) {
        const c = await stripe.customers.retrieve(obj.customer);
        email = c && c.email;
      }
      await setStatus(email, "canceled");
    }
  } catch (e) {
    // acknowledge receipt so Stripe doesn't retry forever; log for inspection
    console.error("webhook handling error", e);
  }
  res.json({ received: true });
};

// Vercel: don't let the platform pre-parse the body — Stripe needs the raw bytes.
module.exports.config = { api: { bodyParser: false } };
