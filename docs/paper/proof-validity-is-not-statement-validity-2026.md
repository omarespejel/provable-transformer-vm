# Proof Validity Is Not Statement Validity: Typed Boundaries for zkML Proof Artifacts

**Omar Espejel**  
Starknet Foundation

**Abdelhamid Bakhta**  
StarkWare

*June 2026 draft*

## Abstract

You verified the proof. Now what exactly did you verify?

That question is easy to skip in zkML systems. A proof verifier can correctly
accept a proof while the surrounding application attaches that proof to the
wrong model, the wrong input, the wrong output, the wrong numeric policy, the
wrong verifier domain, or the wrong operational event. The proof is valid, but
the public statement around it is not.

This paper separates those two layers. Proof validity asks whether a proof
satisfies a verifier relation for a public instance. Statement validity asks
what claim the proof is allowed to mean after another system consumes it as a
receipt.

The contribution is a typed statement-boundary discipline for zkML proof
artifacts. Such a boundary binds the proof bytes to the model surface, input,
output, numeric policy, verifier domain, source artifact handles, replay
dependencies, and application claim that the next layer is allowed to rely on.
In our system we call this boundary object a **Tablero**. The name is secondary.
The main point is the boundary: a proof artifact should not travel through an
application stack without the statement it is allowed to certify.

This is not a new proving protocol and not a claim that existing proof systems
are unsound. It is a systems rule for using proof artifacts safely. It
complements the companion proof-pressure paper: proof-pressure boundaries choose
efficient proof objects; typed statement boundaries preserve what those proof
objects mean.

---

## 1. The Question After Verification

Most zkML demos have a dramatic moment: the proof verifies.

That moment matters. It means the proof system accepted the proof for some
relation and some public instance. But it is not the end of the story. A user,
agent, exchange, auditor, or deployment system rarely wants only that narrow
fact. It wants to act on a larger claim:

> This model, on this input, produced this output, under this numeric policy,
> for this application event.

Those are not the same claim.

The verifier might have checked a bounded attention relation. The application
might say that a particular model answered a particular prompt. The verifier
might have checked table membership for a quantized Softmax policy. The
application might say that a deployment obeyed a policy. The verifier might have
checked a proof under one domain. The application might reuse the proof under a
different domain.

The failure is not that the proof system is weak. The failure is that the
application has quietly changed the sentence attached to the proof.

---

## 2. A Concrete Example

Imagine a defense audit log for an autonomous sensor workflow.

A model receives a sensor crop. The system records a proof receipt. Later, an
operator reads the receipt as:

> The approved model reviewed this frame and classified the object as harmless
> under the current rules of engagement.

Now ask what the proof actually bound.

If the proof only says that some committed tensor passed some local classifier
relation, that is useful but incomplete. It does not by itself bind the approved
model version. It does not bind the sensor frame. It does not bind the timestamp
or deployment zone. It does not bind the numeric policy used to quantize the
model. It does not bind the policy rule that makes the decision operationally
meaningful.

The proof can verify and still be the wrong receipt for the operational claim.

This is the same distinction high-assurance engineering already understands. A
component test is not a mission authorization. A signed file is not the same as
a correct deployment record. A valid checksum does not tell you whether you are
looking at the right object for the job. Cryptographic proof artifacts need the
same discipline.

---

## 3. What Goes Wrong

The mistake is to treat proof verification as if it automatically carries all
the surrounding context.

Here are common relabeling failures.

| Verified artifact | Wrong public meaning attached later |
|---|---|
| proof for model surface A | claimed as model surface B |
| proof for input commitment X | shown as proof for prompt or frame Y |
| proof for output commitment O | displayed beside output O' |
| proof under verifier domain D | accepted under verifier domain D' |
| proof under numeric policy P | marketed as exact real-valued inference |
| proof for table identity T | reused with a different table or range policy |
| proof for a local computation | treated as a deployment authorization |
| proof for one artifact version | attached to a later regenerated artifact |

Every row has the same shape. The proof may be locally valid. The public claim
is not bound to what the proof actually checked.

This is why "the verifier returned true" is not a complete receipt interface.
It is one field inside a larger receipt.

---

## 4. The Small Question and the Big Question

A proof verifier answers the small question:

```text
Does proof P verify for verifier domain D and public instance I?
```

A zkML application asks the big question:

```text
Does artifact A justify claim C about model M, input X, output Y,
numeric policy N, verifier domain D, and event E?
```

The small question is necessary. It is not sufficient.

The gap between those questions is where statement validity lives. Statement
validity is not a vague legal wrapper. It is the engineering layer that says
which bytes, commitments, identifiers, and policies must be bound together
before a downstream system is allowed to rely on the proof.

---

## 5. A Typed Statement Boundary

The fix is to make the boundary explicit.

A typed statement boundary is an object that travels with the proof and says:

1. what proof artifact is being consumed;
2. which verifier domain is allowed to verify it;
3. which model surface or checkpoint it belongs to;
4. which input and output commitments it binds;
5. which numeric policy it assumes;
6. which lookup tables, source artifacts, and replay dependencies it summarizes;
7. which application claim the next layer may make from it;
8. what the artifact does not certify.

The boundary should be typed because these fields are not interchangeable. A
model commitment is not an input commitment. A verifier-domain identifier is not
a policy identifier. A source-artifact digest is not an output claim. Treating
them as generic strings invites exactly the relabeling failure the boundary is
supposed to prevent.

The boundary should also be checked before acceptance. A verifier or application
should not accept a zkML receipt only because the raw proof verifies. It should
accept only when both statements are true:

```text
Verify(proof, verifier_domain, public_instance) = true
Validate(statement_boundary, application_claim) = true
```

That second line is the point of this paper.

There is one important security distinction. Some fields are **hard-bound**:
they appear in the proof's public instance, or the public instance contains a
commitment that the verifier or receipt validator checks against them. Other
fields are only envelope metadata. Those fields can be useful for routing,
display, and audit logs, but they are advisory until validation ties them back
to a hard-bound commitment. A serious receipt should make that distinction
visible.

---

## 6. Where Tablero Enters

In our system, we call this typed boundary object a **Tablero**.

The word is not meant to sell a new prover. Tablero is not a proof system, not a
new commitment scheme, and not a replacement for the verifier. It is the receipt
boundary around proof artifacts: proof bytes plus the statement they are allowed
to mean.

A Tablero-style boundary records the proof digest, verifier domain, statement
commitment, source handles, replay skips, model surface, numeric policy, input
commitment, output commitment, and non-claims. The exact field set depends on
the application. The rule does not:

> If the next layer relies on a fact, the boundary must bind that fact.

This is why the concept belongs next to zkML proof architecture. Once proofs are
split, fused, wrapped, exported, or passed to agents, the system needs a typed
object that preserves meaning across those movements.

---

## 7. How This Connects to Proof-Pressure Boundaries

The companion paper
[Proof-Pressure Boundaries for STARK-Native Transformer Inference](proof-pressure-boundaries-for-stark-native-transformers-2026.md)
studies where transformer work should share a proof object. It asks a
performance-architecture question:

> Where should attention arithmetic, lookup-heavy work, and statement plumbing
> share proof-system structure?

This paper asks the correctness question that follows:

> After choosing a proof boundary, what exactly is the resulting proof artifact
> allowed to mean?

Those two questions belong together. If a transformer surface is split across
several proof objects, typed boundaries preserve the claim between them. If a
surface is fused into one larger proof object, the fused artifact still needs a
typed boundary. Fusion changes how much proof plumbing is shared. It does not
remove the need to bind the claim.

---

## 8. Minimal Field Set

A practical zkML statement boundary should bind at least these fields when they
are part of the public claim.

| Field | What it prevents |
|---|---|
| proof digest | swapping the proof artifact after verification |
| verifier domain | verifying under one domain and accepting under another |
| verifier key or relation handle | changing the relation being checked |
| model surface or checkpoint commitment | relabeling one model as another |
| input commitment | attaching the proof to the wrong prompt, frame, or tensor |
| output commitment | displaying a different answer beside a valid proof |
| numeric policy | hiding quantization, rounding, range, or approximation choices |
| lookup-table identity | reusing membership evidence for the wrong table |
| source artifact handles | losing provenance for generated proof inputs |
| replay dependencies | skipping reconstruction work the boundary did not summarize |
| application claim | letting the same proof mean different things in different contexts |
| non-claims | preventing the receipt from silently growing in scope |

The list is not universal. A medical workflow, defense workflow, exchange
listing workflow, and agent-settlement workflow will bind different operational
fields. But the discipline is the same: every relied-on fact has to appear in
the typed boundary, directly or through a commitment.

---

## 9. What This Does Not Claim

This paper does not claim that proof verification is unimportant. It is the
cryptographic core.

It does not claim that existing proof systems are broken. The gap described here
is usually above the proof system, in the receipt and application layer.

It does not claim a complete production AI assurance framework. A full system
may also need model governance, data provenance, policy review, software
deployment controls, incident logs, human approval, and external audit.

It does not claim that every zkML receipt should use the same schema. The schema
should follow the claim being made.

It does claim one narrow thing:

> A proof artifact used as a receipt needs a typed statement boundary. Without
> that boundary, proof validity can be mistaken for statement validity.

---

## 10. Reviewer Checklist

A reviewer should be able to ask the following questions and find exact answers
in the boundary object.

1. Which proof bytes were verified?
2. Which verifier domain accepted them?
3. Which verifier relation or key was used?
4. Which model surface or checkpoint is being claimed?
5. Which input was bound?
6. Which output was bound?
7. Which numeric policy was used?
8. Which lookup tables or range policies were assumed?
9. Which source artifacts produced the proof inputs?
10. Which reconstruction work may a later layer skip?
11. Which application claim is allowed?
12. Which claims are explicitly out of scope?

If any relied-on answer is missing, the proof may still be valid, but the
receipt is incomplete.

---

## 11. Reproduction and Scope

This companion is a statement-boundary paper. It introduces no new proof-size
or timing numbers. Its reproduction surface is therefore the paper preflight
itself:

```bash
./scripts/run_paper_preflight_suite.sh
```

The checked proof-pressure artifacts already bind scoped transformer surfaces to
their verifier domains, source handles, target identifiers, statement
commitments, and input-output commitments. They are not full production model
receipts. A production receipt would extend the same boundary pattern to the
model checkpoint, tokenizer, deployment policy, source event, and operational
claim.
