# THE VISCOUNT'S VIGIL — Complete Walkthrough & Dialogue Guide
### Every Act, Timed Event, NPC Exchange & All 7 Endings (A–G)

---

## Table of Contents
1. [Prologue & Act 0 — The Carriage](#prologue--act-0--the-carriage)
2. [Act 1 — The Estate Steps (Reynard)](#act-1--the-estate-steps-reynard)
3. [Act 2 — The Party Floor & Timed Events](#act-2--the-party-floor--timed-events)
4. [Act 3 — The Toast & All 7 Endings](#act-3--the-toast--all-7-endings)
   - [Ending A — Full Victory](#ending-a--full-victory-best-ending)
   - [Ending B — Pyrrhic Victory](#ending-b--pyrrhic-victory)
   - [Ending C — The Wrong Target](#ending-c--the-wrong-target)
   - [Ending D — The Dungeon](#ending-d--the-dungeon)
   - [Ending E — The Conspiracy (Easter Egg)](#ending-e--the-conspiracy-easter-egg)
   - [Ending F — Total Failure](#ending-f--total-failure)
   - [Ending G — Self-Sacrifice](#ending-g--self-sacrifice)

---

## Prologue & Act 0 — The Carriage

### Prologue (`Dawn`)
Scripted vision sequence introducing **The Sight**: candlelight, a glass of deep red wine, a black-gloved hand, a smiling woman, and the sound of shattering glass.

### Act 0 — Talking to Aldous (`5:00 PM`)
Choose **`SPEAK`** (*Knock on the roof panel and speak to Aldous*).

- **You:** *"What do you think of the peace treaty?"*
  - **Aldous:** *"I reckon it’s a relief that the fighting’s over after a decade. The lads and lasses in the villages have had enough of the loss. A peace that lets folks breathe again feels right."*
- **You:** *"Have you heard anything about the Duke's conduct during the war?"*
  - **Aldous:** *"I’ve heard the word in the taverns that some folk are bitter about the Duke’s orders. They say men were sent out on missions that, in their view, could’ve been avoided."* *(Opens the Duke's private guilt thread later.)*
- **You:** *"How long until we arrive?"*
  - **Aldous:** *"We should be there in about half an hour, my lord. We’ll be past the gates before the clock strikes seven."*
- Type `leave` or `done` to arrive at the estate gates (`6:58 PM`).

---

## Act 1 — The Estate Steps (Reynard)

**Important:** Do **NOT** mention your dream/vision to Reynard (`SL` rises and he uses it to discredit you in Act 3). Do **NOT** accuse him of murder/poison (`SL >= 3` triggers Ending D immediately).

- **Reynard:** *"Lord Viscount. His Grace will be glad you've come — I'll see you through to the hall personally. Was the road kind to you tonight?"*
- **You:** *"How long have you served the Duke, Reynard? Thirty years?"*
  - `▲ Reynard seems warmer toward you.` (`FL = 1`, `reynard_met_warmly = True` — required later for his testimony in Ending A.)
  - **Reynard:** *"My tenure has spanned thirty years, my lord. I have endeavored to serve the household with unwavering fidelity."*
- **You:** *"What is being served tonight? Is there anything special prepared for the feast or drinks?"*
  - **Evidence Noted:** *Reynard mentioned the ceremonial wine. Very particular about it staying sealed until the toast.*
  - **Reynard:** *"For the toasts, a ceremonial wine has been brought from the eastern court, its provenance verified by the household. His Grace gave very strict instructions that it remain sealed until the treaty is signed."*
- Press **Enter** on a blank line to walk into the Main Hall (`7:00 PM`).

---

## Act 2 — The Party Floor & Timed Events

### Timed Events Schedule (Watch the Clock!)
| Time / Window | Event | What Happens |
|---|---|---|
| **30–60 min after Act 2 start** (20-min window) | **The Balcony Vision** | Visiting **The Balcony** during this window triggers a vision of Reynard at the cellar door with a woman wearing a **silver ring with a red stone**. |
| **8:15 PM – 8:55 PM** (`clock 75–115`) | **Ophelia's Footman Whisper** | Moving on the Party Floor reveals **Ophelia** pressing a folded parchment into a footman's palm near the east archway. |
| **9:15 PM+** (`clock >= 135`) | **Cellar Bottles Moved** | If you visit **The Cellar** at `9:15 PM` or later, the eastern bottles have already been carried upstairs — you miss the wax-seal inspection and find only empty racks and wax shavings. |
| **9:30 PM** (`<= 30 min` left) | **Final Bell** | A bell rings and servants begin setting out glasses. |
| **After 2+ conspiracy stations** | **Overheard Passphrase** | You overhear: *"...the harvest was good this year..." / "...better than the war years..."* |

---

### Station-by-Station Dialogue & Clues

#### 1. Lord Fenwick (Opening Hub — Easy Talker)
- **You:** *"Who here actually supported the war most and profited?"*
  - **Unlocks:** `House Marrow Table` & `House Vantrell Table`.
  - **Lord Fenwick:** *"Ah, the Vantrells, of course—Cassian’s always been the charming face of the war effort, supplying arms and rations, while Ophelia kept the books tighter than a miser’s purse. Their income’s been cut in half."*
- **You:** *"What do you know about the foreign delegation?"*
  - **Unlocks:** `Foreign Delegation`.
  - **Lord Fenwick:** *"Counselor Demir has been a bit on edge tonight—caught in a hushed chat with a military man just before anyone noticed."*
- **You:** *"What do you really think of the Duke?"*
  - **Lord Fenwick:** *"Aldric was the one who sent men into those costly battles... a mix of conviction and penance."*

#### 2. Kitchen & Cellar (Go BEFORE `9:15 PM`!)
- **You (to Mrs. Alwen):** *"Did Reynard give you any special orders about the wine?"*
  - **Evidence Noted:** *Reynard kept the gift wine completely out of the kitchen. No independent verification of the seal was possible.*
  - **Mrs Alwen:** *"Very odd, my lord — Reynard ordered the eastern gift wine kept entirely away from the kitchens! We never even got to inspect the wax seals."*
- **You (to Mrs. Alwen):** *"Two of Reynard's cellar staff fell ill today, I heard?"*
  - **Evidence Noted:** *Two cellar staff fell suddenly and conveniently ill this afternoon — the ones who would have handled the gift wine.*
  - **Mrs Alwen:** *"Willem and Dorse both took suddenly and violently ill around four o'clock today! Both fit as draft horses at lunch."*
- **Go down to the Cellar (`YES` → `BOTH`):**
  - **Evidence Noted:** *The gift wine's seal was broken and resealed. Someone tampered with it.*
  - **Evidence Noted:** *Reynard's handwriting in the cellar log. He moved the wine to the serving rack himself today.*

#### 3. The Balcony (During the Vision Window)
- **Vision:** *"Reynard — carrying something wrapped in cloth... Behind him the door is held open by a gloved hand. A woman's hand. A ring catches the light — silver, red stone."*
- **Evidence Noted:** *Second vision — Reynard and a woman at the cellar this afternoon. The ring is identifiable.*

#### 4. House Marrow Table (Lady Brienne)
- **You:** *"I'm sorry about your father."* (`▲ Lady Brienne seems warmer toward you.`)
- **Lady Brienne:** *"My father held the Verenmark crossing for four days on orders from above. No relief arrived. He died doing his duty, and tonight they drink wine over his bones."*
- *(If you visited Vantrell first, a servant delivers an anonymous threat note: `"Leave before midnight. For your health."`)*

#### 5. House Vantrell Table (Cassian & Ophelia — Guarded)
Address **Cassian** or **Ophelia** by name. Ophelia is guarded and will **not** slip up on turn 1 — engage her calmly for at least 2 turns without accusing her directly.
- **You:** *"House Vantrell was heavily involved in the war effort. The peace must cut into your income."*
  - **Evidence Noted:** *Cassian's peace speech is too polished.*
  - **Lord Cassian:** *"An adjustment is natural when a long war ends, Viscount! One adapts with pleasure."*
- **You:** *"Lady Ophelia, you've been very quiet tonight."*
  - **Lady Ophelia:** Observes the room coolly without giving much away yet.
- **You:** *"Lady Ophelia, I suppose you notice every detail of how the household prepares for an evening like this."*
  - **Evidence Noted:** *Ophelia mentioned in passing that Reynard was in the cellar this afternoon.*
  - **Lady Ophelia:** *"Reynard is a remarkable man... He was down in the cellars this afternoon, quite particular about the wine arrangements."*
- **You:** *"Lady Ophelia, that is a striking silver ring with a red stone you are wearing."*
  - **Evidence Noted:** *Ophelia's ring matches the vision exactly. She was at the cellar door with Reynard this afternoon.*
  - **Lady Ophelia:** *"A modest family heirloom, my lord. Nothing of historical import. Why do you ask?"*

#### 6. Lady Isolde (Crucial Safety Net)
Build `FL >= 2` first by showing genuine perception before warning her:
- **You:** *"You seem to carry the burden of this peace treaty with great grace. What does it cost you?"* (`FL +2`)
- **You:** *"I am truly glad you are here, Isolde. I see how much you care for this peace."* (`FL = 3`)
- **You:** *"I believe the ceremonial wine tonight has been tampered with. Do not drink from it at the toast."*
  - **Evidence Noted:** *Isolde warned about the wine. She will not drink it at the toast.*
  - **Lady Isolde:** *"If your trust is true, I will quietly set my glass down."*

#### 7. Foreign Delegation (Demir & Kavir — Requires Patience)
Demir will **not** confess in a single line; earn `FL >= 2` and speak to him at least twice:
- **You:** *"Counselor Demir, you have my word of complete discretion. What is troubling you?"*
  - **Counselor Demir:** *"I appreciate your discretion, Viscount... There are delicate personal matters concerning the Prince's arrangements that cannot reach Lady Isolde's family before the signing."*
- **You:** *"I am not here to expose anyone, Counselor. Tell me plainly between us — is the treaty itself in danger?"*
  - **Evidence Noted:** *Demir fully cleared — hiding the Prince's personal scandal, not a murder plot. The delegation is innocent.*
  - **Counselor Demir:** *"If you swear complete confidentiality... It is the Prince. He has accumulated staggering gambling debts, and a romantic liaison that would ruin the marriage treaty if exposed."*

---

## Act 3 — The Toast & All 7 Endings

---

### Ending A — Full Victory (Best Ending)
**Requirements:** Stop the wine (`conviction >= 3`) + call out Ophelia's tell + have Reynard `FL >= 1` (`reynard_met_warmly`) and persuade him to testify.

1. **Confrontation Turn 1:**
   - **You:** *"Your Grace, stop! The seal on that eastern wine was reapplied — the wax doesn't match — and both cellar staff fell mysteriously ill at four o'clock!"*
   - **Duke Aldric:** *"You speak with unusual certainty. If there is genuine cause to suspect the ceremonial draught, I will have it placed under precautionary guard."*
2. **Confrontation Turn 2:**
   - **You:** *"The cellar log shows those bottles were moved today, and Ophelia Vantrell was seen at the cellar door!"*
   - **Duke Aldric:** *"Hold the wine. Now. All of it."*
3. **Ophelia's Tell:** Narration shows Ophelia's hand reaching toward a glass and freezing.
   - **You:** *"Her! Lady Ophelia Vantrell — she knows exactly what is in that wine!"*
   - **Duke Aldric:** *"Guards. Both of them. Now."* (`Ophelia` & `Cassian` arrested.)
4. **Reynard's Final Moment:**
   - **You:** *"Why, Reynard? Thirty-one years of service."*
   - **Reynard:** Reveals his son died at the Verenmark crossing on the Duke's orders.
   - **You:** *"You could still do something right. Testify. Tell the Duke everything."*
   - **Reynard:** *"He'll never forgive me."* → **You:** *"He'll have to try."*
   - Reynard confesses publicly, collapsing Cassian's legal defense. **Ending A achieved.**

---

### Ending B — Pyrrhic Victory
**Requirements:** Stop the wine (or Isolde saves herself), **do NOT** name Ophelia during her tell.
- When Ophelia's hand freezes over the glass and the game asks *"What do you do?"*, press **Enter** (say nothing) or talk about something else.
- Ophelia slips out into the night and escapes the country. Cassian is arrested, but without Ophelia in custody his legal defense may hold. **Ending B achieved.**

---

### Ending C — The Wrong Target
**Requirements:** Gather at least 1 piece of evidence (`evidence_score() >= 1`), **fail** to stop the toast in Act 3, and **do NOT** have Isolde's wine-warning trust (`isolde_will_avoid_wine == False`).
- For example, focus on protecting **Lady Brienne** (the decoy target) and never build the case against the wine/Reynard.
- The toast proceeds. At midnight, **Isolde** collapses. She survives barely, the treaty is postponed indefinitely, and no culprits are caught. **Ending C achieved.**

---

### Ending D — The Dungeon
**Any of these 4 triggers leads to Ending D:**
1. **Act 1:** Raise Reynard's suspicion to `SL >= 3` by accusing him of murder/poison/conspiracy on arrival.
2. **Act 1 (Easter Egg Fail):** Speak the passphrase to Reynard, then fail his corridor interrogation (`credibility < 5`).
3. **Act 2 or 3:** Accuse **Reynard** directly to the **Duke** while your `evidence_score() < 3` (the Duke trusts 31 years of service and privately informs Reynard, who has you locked away).
4. **Act 3:** Attempt a physical intercept (`"I grab the glass!"`) when **both** `Isolde FL < 2` and `Brienne FL < 2`.

---

### Ending E — The Conspiracy (Easter Egg)
**Requirements:** Speak the secret passphrase **`"The harvest was good this year."`** to Reynard in **Act 1** (discovered on a second playthrough after overhearing it in Act 2).
- **Reynard:** *"...Better than the war years."*
- He pulls you into a private corridor for a 4-question interrogation:
  - Answer calmly and specifically like a genuine operative: name **House Vantrell**, the **ceremonial wine**, and the plan to **implicate the foreign delegation**.
  - **Pass (`credibility >= 5`):** Unlocks the `easter_egg_activated` path into Act 2 with insider knowledge.
  - **Fail (`credibility < 5`):** Guards detain you immediately (**Ending D**).

---

### Ending F — Total Failure
**Requirements:** Gather **0** key conspiracy clues (`evidence_score() == 0`), do **not** warn Isolde at `FL >= 2`, and stay silent (blank `Enter` on all turns) or fail to persuade the Duke during Act 3.
- The toast proceeds uninterrupted. Isolde dies three days later, **Counselor Demir** is framed, the treaty collapses in 8 days, and House Vantrell resumes war supply contracts. **Ending F achieved.**

---

### Ending G — Self-Sacrifice
**Requirements:** During the Act 3 climax confrontation (when you lack proof or time), type an explicit sacrifice action:
- **You:** *"I reach across, lift Isolde's glass, and drink it myself."*
- **Lady Isolde:** *"What — what are you—"*
- The poison is slow-acting; you survive after three days with the physician, while the disruption rattles Ophelia into exposing herself the next morning. **Ending G achieved.**
