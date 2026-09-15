// gym_web/js/i18n.js
// Translation-by-value: exercise files keep emitting English strings
// unchanged. This module intercepts the string at speak/display time.


export function tGoStart(setNum, exerciseName) {
  return currentLang === "hi"
    ? `शुरू! सेट ${setNum}, अपनी ${exerciseName} शुरू करें।`
    : `Go! Set ${setNum}, start your ${exerciseName}.`;
}
export function tGetReady(setNum) {
  return currentLang === "hi" ? `सेट ${setNum} के लिए तैयार हो जाइए` : `Get ready for set ${setNum}`;
}


export const SUPPORTED_LANGS = { en: "English", hi: "हिन्दी" };

let currentLang = localStorage.getItem("gymAgentLang") || "en";

export function getLang() { return currentLang; }

export function setLang(lang) {
  if (!SUPPORTED_LANGS[lang]) return;
  currentLang = lang;
  localStorage.setItem("gymAgentLang", lang);
  document.dispatchEvent(new CustomEvent("langchange", { detail: lang }));
}

// Flat EN -> translated lookup. Exact-string match (case-sensitive).
// Add languages by adding a new top-level key.
const DICT = {
  hi: {
    // ── Generic engine lines (prototype.html inline strings) ──
    "Correct your position.": "अपनी स्थिति ठीक करें।",
    "Hold the position!": "स्थिति बनाए रखें!",
    "Get ready for": "तैयार हो जाइए",
    "Workout stopped.": "वर्कआउट रोका गया।",
    "Paused.": "रोका गया।",
    "Resuming.": "फिर से शुरू।",
    "Workout complete! Great job!": "वर्कआउट पूरा! बहुत बढ़िया!",
    "Whoa, are you okay? Press enter when you're ready to continue.":
      "अरे, क्या आप ठीक हैं? जारी रखने के लिए तैयार होने पर एंटर दबाएँ।",
    "Let's get back into position.": "फिर से सही स्थिति में आते हैं।",
    "Step into frame - I can't see you clearly.":
      "कैमरे के सामने आइए - मैं आपको साफ़ नहीं देख पा रहा।",
    "No person detected — step into frame.":
      "कोई व्यक्ति नहीं मिला — कैमरे के सामने आइए।",
    "Keep your tracked joints in frame.":
      "अपने ट्रैक किए जा रहे जोड़ों को फ्रेम में रखें।",

    // ── Common per-exercise form cues (repeat across many files) ──
    "Push your knees outward.": "अपने घुटनों को बाहर की ओर धकेलें।",
    "Keep your elbows pinned to your sides. Don't let them swing.":
      "अपनी कोहनियों को शरीर से सटाकर रखें, उन्हें हिलने न दें।",
    "Keep your back flat and chest up. Avoid rounding your spine.":
      "पीठ सीधी और छाती ऊपर रखें, रीढ़ को गोल न होने दें।",
    "Fully extend your arms overhead at the top.":
      "ऊपर पूरी तरह भुजाएँ सीधी करें।",
    "Push up evenly with both arms. Keep your movement balanced.":
      "दोनों भुजाओं से बराबर ज़ोर लगाएँ, संतुलन बनाए रखें।",
    "Lower your hips. Keep your body in a straight plank line.":
      "कूल्हे नीचे लाएँ, शरीर को सीधी रेखा में रखें।",
    "Engage your core. Don't let your hips drop.":
      "पेट कसें, कूल्हों को नीचे न गिरने दें।",
    "Keep your knees straight and locked throughout the raise.":
      "उठाते समय घुटने सीधे और लॉक रखें।",
    "Sink lower into your lunge until your thigh is parallel to the floor.":
      "अपने लंज में और नीचे जाएँ जब तक जांघ फर्श के समांतर न हो।",
    "Take a wider step out to the side before lunging.":
      "लंज से पहले बगल में चौड़ा कदम रखें।",
    "Drive your knees up higher until your thighs are parallel to the floor.":
      "घुटनों को और ऊँचा उठाएँ जब तक जांघ फर्श के समांतर न हो।",
    "Raise your arms fully above your head.":
      "अपनी भुजाएँ पूरी तरह सिर के ऊपर उठाएँ।",
    "Jump your feet out wider to at least shoulder width.":
      "पैरों को कम से कम कंधों जितना चौड़ा फैलाएँ।",
    "Keep your hips in line with your shoulders and plank.":
      "कूल्हों को कंधों और प्लैंक के साथ एक सीध में रखें।",
    "Drive your knee closer toward your chest.":
      "घुटने को छाती के और पास लाएँ।",
    "Dip lower until your elbows are at a 90-degree angle.":
      "और नीचे जाएँ जब तक कोहनी 90 डिग्री पर न हो।",
    "Keep your elbows tucked back close to your body.":
      "कोहनियों को शरीर के पास सटाकर रखें।",
    "Not counted.": "गिना नहीं गया।",
    "Fix your form and try again.": "अपनी मुद्रा ठीक करें और फिर से कोशिश करें।",

    // Add inside DICT.hi in i18n.js
    "Choose an exercise — real-time form check prototype": "एक व्यायाम चुनें — रीयल-टाइम फ़ॉर्म जाँच प्रोटोटाइप",
    "REPS / SET": "रेप्स / सेट",
    "TOTAL SETS": "कुल सेट",
    "Start Camera": "कैमरा शुरू करें",
    "Loading model…": "मॉडल लोड हो रहा है…",
    "Loading MediaPipe model…": "मीडियापाइप मॉडल लोड हो रहा है…",
    "Requesting camera…": "कैमरे की अनुमति माँगी जा रही है…",
    "Finish / Restart": "समाप्त करें / फिर से शुरू करें",
    "Catch your breath before the next set.": "अगले सेट से पहले सांस लें।",
    "Workout Complete! 🎉": "वर्कआउट पूरा! 🎉",
    "Point the phone upright so your full body is visible, feet to head, facing the camera.":
    "फ़ोन को सीधा रखें ताकि आपका पूरा शरीर, सिर से पैर तक, कैमरे के सामने दिखे।",
    "Rotate the phone to landscape for a clear side-view of your body.":
    "अपने शरीर का साफ़ साइड-व्यू पाने के लिए फ़ोन को लैंडस्केप में घुमाएँ।",
    "Position the phone so your full body is visible (lying or side view is fine).":
    "फ़ोन को इस तरह रखें कि आपका पूरा शरीर दिखे (लेटकर या साइड व्यू भी ठीक है)।",
    "Hold still...": "स्थिर रहें...",
    "SET": "सेट",
    "REPS": "रेप्स",
    "FORM": "फॉर्म",
    "NOT COUNTED — FIX FORM": "नहीं गिना गया — फॉर्म ठीक करें",
    "needs your phone in LANDSCAPE — rotate it sideways for a clear side-view profile.":
    "के लिए फ़ोन को LANDSCAPE में चाहिए — साफ़ साइड-व्यू के लिए इसे बगल में घुमाएँ।",
    "needs your phone in PORTRAIT — rotate it upright and step back so your full body is visible.":
    "के लिए फ़ोन को PORTRAIT में चाहिए — इसे सीधा रखें और पीछे हटें ताकि पूरा शरीर दिखे।",
    "No person detected — step into frame.": "कोई व्यक्ति नहीं मिला — फ्रेम में आइए।",
    "Keep your tracked joints in frame.": "ट्रैक किए जा रहे जोड़ों को फ्रेम में रखें।",

  },
};



// Exercise display-name translations, keyed by the exercise's registry
// key (ex.constructor.key) — NOT looked up by displayName text, since
// keys are stable and unambiguous where English strings could collide.
const EXERCISE_NAMES = {
  hi: {
    squat: "स्क्वाट",
    push_up: "पुश अप",
    bicep_curl: "बाइसेप कर्ल",
    hammer_curl: "हैमर कर्ल",
    shoulder_press: "शोल्डर प्रेस",
    lateral_raise: "लेटरल रेज़",
    lunge: "लंज",
    side_lunge: "साइड लंज",
    deadlift: "डेडलिफ्ट",
    glute_bridge: "ग्लूट ब्रिज",
    calf_raise: "काफ रेज़",
    leg_raise: "लेग रेज़",
    plank: "प्लैंक",
    wall_sit: "वॉल सिट",
    jumping_jack: "जंपिंग जैक",
    high_knees: "हाई नीज़",
    mountain_climber: "माउंटेन क्लाइंबर",
    tricep_dip: "ट्राइसेप डिप",
    horizontal_press: "हॉरिज़ॉन्टल प्रेस",
    bent_over_row: "बेंट-ओवर रो",
    bench_press: "बेंच प्रेस",
    fly: "फ्लाई",
    front_raise: "फ्रंट रेज़",
    rear_delt_fly: "रियर डेल्ट फ्लाई",
    overhead_tricep_extension: "ओवरहेड ट्राइसेप एक्सटेंशन",
    tricep_kickback: "ट्राइसेप किकबैक",
    lat_pulldown: "लैट पुलडाउन",
    sit_up: "सिट अप",
    russian_twist: "रशियन ट्विस्ट",
    leg_extension: "लेग एक्सटेंशन",
    leg_curl: "लेग कर्ल",
    leg_press: "लेग प्रेस",
    preacher_curl: "प्रीचर कर्ल",
    ez_bar_curl: "ईज़ी-बार कर्ल",
    barbell_curl: "बारबेल कर्ल",
    cable_curl: "केबल कर्ल",
    barbell_back_squat: "बारबेल बैक स्क्वाट",
    hack_squat: "हैक स्क्वाट",
    barbell_calf_raise: "बारबेल काफ रेज़",
    cable_calf_raise: "केबल काफ रेज़",
    barbell_overhead_press: "बारबेल ओवरहेड प्रेस",
    machine_shoulder_press: "मशीन शोल्डर प्रेस",
    incline_bench_press: "इनक्लाइन बेंच प्रेस",
    chest_press_machine: "चेस्ट प्रेस मशीन",
    incline_push_up: "इनक्लाइन पुश अप",
    diamond_push_up: "डायमंड पुश अप",
    pec_deck: "पेक डेक",
    seated_cable_row: "सीटेड केबल रो",
    cable_lateral_raise: "केबल लेटरल रेज़",
    cable_chest_fly: "केबल चेस्ट फ्लाई",
    bench_dip: "बेंच डिप",
  },
};

/** Translate an exercise's display name by its registry key (falls back
 * to the English displayName if no translation exists yet). */
export function tExercise(key, fallbackName) {
  if (currentLang === "en" || !key) return fallbackName;
  return EXERCISE_NAMES[currentLang]?.[key] || fallbackName;
}



/** Translate an exact English string; falls back to the original text. */
export function t(text) {
  if (currentLang === "en" || !text) return text;
  return DICT[currentLang]?.[text] || text;
}

/** Templated helper for dynamic lines that contain numbers. */
export function tRep(n) {
  return currentLang === "hi" ? `रेप ${n}` : `Rep ${n}`;
}
export function tSetGo(n) {
  return currentLang === "hi" ? `सेट ${n}, शुरू!` : `Set ${n}, Go!`;
}
export function tSetComplete(n) {
  return currentLang === "hi"
    ? `सेट ${n} पूरा हुआ! आराम करें।`
    : `Set ${n} complete! Take a rest.`;
}
export function tRemaining(sec) {
  return currentLang === "hi" ? `${sec} सेकंड बचे हैं` : `${sec} seconds remaining`;
}

/** Pick the best available browser TTS voice for the current language. */
export function pickVoice() {
  const wantLang = currentLang === "hi" ? "hi" : "en";
  const voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
  return voices.find(v => v.lang.toLowerCase().startsWith(wantLang)) || null;
}
