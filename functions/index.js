
const { onValueCreated } = require('firebase-functions/v2/database');
const admin = require('firebase-admin');
admin.initializeApp();

const GIFT = 50;
const TXID = 'BYENVENI-AUTO';
const MAX_AGE_MS = 3 * 86400000;

exports.welcomeGift = onValueCreated(
  { ref: '/paymentRequests/{uid}/welcome' },
  async (event) => {
    const uid = event.params.uid;
    const req = event.data.val() || {};
    const db = admin.database();
    const reqRef = db.ref('paymentRequests/' + uid + '/welcome');
    const reject = (reason) => reqRef.update({ status: 'rejected', reason, verifiedAt: admin.database.ServerValue.TIMESTAMP });
    if (req.status !== 'pending') return;
    if (Number(req.amount) !== GIFT || req.txid !== TXID) return reject('Kado pa valab');
    let user;
    try { user = await admin.auth().getUser(uid); } catch (e) { return reject('Kont pa jwenn'); }
    if (!user.providerData || user.providerData.length === 0) return reject('Kont anonim');
    const created = Date.parse(user.metadata.creationTime);
    if (!created || Date.now() - created > MAX_AGE_MS) return reject('Kont lan pa nouvo');
    const creditRef = db.ref('wallets/' + uid + '/credits/welcome');
    const tx = await creditRef.transaction((cur) =>
      cur === null ? { amount: GIFT, ts: admin.database.ServerValue.TIMESTAMP, by: 'server', req: 'welcome', kind: 'welcome' } : undefined
    );
    if (!tx.committed) return reject('Kado deja bay');
    await reqRef.update({ status: 'verified', verifiedAt: admin.database.ServerValue.TIMESTAMP });
  }
);
