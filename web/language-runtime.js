(() => {
  "use strict";
  if (window.AuroraI18n) return;
  const rtl = new Set(["ar","arc","dv","fa","he","khw","nqo","ps","syr","ug","ur","yi"]);
  const languages = [
    ["en","English","us"],["en-GB","English (UK)","gb"],["ar","العربية","ara"],
    ["he","עברית","il"],["fr","Français","fr"],["de","Deutsch","de"],
    ["es","Español","es"],["ru","Русский","ru"],["el","Ελληνικά","gr"],
    ["tr","Türkçe","tr"],["fa","فارسی","ir"],["ur","اردو","pk"],
    ["hi","हिन्दी","in"],["bn","বাংলা","bd"],["zh-CN","简体中文","us"],
    ["ja","日本語","jp"],["ko","한국어","kr"],["pt","Português","br"],
    ["it","Italiano","it"],["nl","Nederlands","nl"],["pl","Polski","pl"]
  ];
  const copy = {
    en:{button:"Language",title:"Language & input",display:"Display language",input:"Keyboard / input source",apply:"Apply language",custom:"Other BCP-47 language tag",voice:"Speak a sample",dictate:"Start dictation",close:"Close",welcome:"Welcome to your desktop.",status:"Choose a display language and an input source."},
    ar:{button:"اللغة",title:"اللغة والإدخال",display:"لغة العرض",input:"لوحة المفاتيح / مصدر الإدخال",apply:"تطبيق اللغة",custom:"رمز لغة BCP-47 آخر",voice:"تشغيل عينة صوتية",dictate:"بدء الإملاء",close:"إغلاق",welcome:"مرحباً بك في سطح المكتب.",status:"اختر لغة العرض ومصدر الإدخال."},
    fr:{button:"Langue",title:"Langue et saisie",display:"Langue d’affichage",input:"Clavier / méthode de saisie",apply:"Appliquer",custom:"Autre identifiant BCP-47",voice:"Lire un exemple",dictate:"Démarrer la dictée",close:"Fermer",welcome:"Bienvenue sur votre bureau.",status:"Choisissez la langue et la méthode de saisie."},
    de:{button:"Sprache",title:"Sprache und Eingabe",display:"Anzeigesprache",input:"Tastatur / Eingabequelle",apply:"Sprache anwenden",custom:"Anderes BCP-47-Sprachtag",voice:"Beispiel sprechen",dictate:"Diktat starten",close:"Schließen",welcome:"Willkommen auf Ihrem Desktop.",status:"Wählen Sie Anzeige- und Eingabesprache."},
    es:{button:"Idioma",title:"Idioma y entrada",display:"Idioma de pantalla",input:"Teclado / método de entrada",apply:"Aplicar idioma",custom:"Otra etiqueta de idioma BCP-47",voice:"Reproducir muestra",dictate:"Iniciar dictado",close:"Cerrar",welcome:"Te damos la bienvenida al escritorio.",status:"Elige el idioma y el método de entrada."},
    ru:{button:"Язык",title:"Язык и ввод",display:"Язык интерфейса",input:"Клавиатура / способ ввода",apply:"Применить язык",custom:"Другой языковой тег BCP-47",voice:"Произнести пример",dictate:"Начать диктовку",close:"Закрыть",welcome:"Добро пожаловать на рабочий стол.",status:"Выберите язык интерфейса и ввода."},
    el:{button:"Γλώσσα",title:"Γλώσσα και είσοδος",display:"Γλώσσα εμφάνισης",input:"Πληκτρολόγιο / μέθοδος εισαγωγής",apply:"Εφαρμογή γλώσσας",custom:"Άλλη ετικέτα BCP-47",voice:"Εκφώνηση δείγματος",dictate:"Έναρξη υπαγόρευσης",close:"Κλείσιμο",welcome:"Καλώς ορίσατε στην επιφάνεια εργασίας.",status:"Επιλέξτε γλώσσα εμφάνισης και εισαγωγής."},
    tr:{button:"Dil",title:"Dil ve giriş",display:"Görüntüleme dili",input:"Klavye / giriş kaynağı",apply:"Dili uygula",custom:"Başka BCP-47 dil etiketi",voice:"Örnek seslendir",dictate:"Dikteyi başlat",close:"Kapat",welcome:"Masaüstünüze hoş geldiniz.",status:"Görüntüleme ve giriş dilini seçin."},
    fa:{button:"زبان",title:"زبان و ورودی",display:"زبان نمایش",input:"صفحه‌کلید / منبع ورودی",apply:"اعمال زبان",custom:"برچسب زبان BCP-47 دیگر",voice:"پخش نمونه گفتار",dictate:"شروع دیکته",close:"بستن",welcome:"به میزکار خود خوش آمدید.",status:"زبان نمایش و ورودی را انتخاب کنید."},
    ur:{button:"زبان",title:"زبان اور اِن پٹ",display:"ڈسپلے کی زبان",input:"کی بورڈ / اِن پٹ ذریعہ",apply:"زبان لاگو کریں",custom:"دوسرا BCP-47 زبان ٹیگ",voice:"نمونہ سنائیں",dictate:"ڈکٹیشن شروع کریں",close:"بند کریں",welcome:"آپ کے ڈیسک ٹاپ پر خوش آمدید۔",status:"ڈسپلے اور اِن پٹ زبان منتخب کریں۔"},
    hi:{button:"भाषा",title:"भाषा और इनपुट",display:"प्रदर्शन भाषा",input:"कीबोर्ड / इनपुट स्रोत",apply:"भाषा लागू करें",custom:"अन्य BCP-47 भाषा टैग",voice:"नमूना बोलें",dictate:"डिक्टेशन शुरू करें",close:"बंद करें",welcome:"आपके डेस्कटॉप पर स्वागत है।",status:"प्रदर्शन और इनपुट भाषा चुनें।"},
    bn:{button:"ভাষা",title:"ভাষা ও ইনপুট",display:"প্রদর্শনের ভাষা",input:"কীবোর্ড / ইনপুট উৎস",apply:"ভাষা প্রয়োগ করুন",custom:"অন্য BCP-47 ভাষা ট্যাগ",voice:"নমুনা বলুন",dictate:"ডিকটেশন শুরু করুন",close:"বন্ধ করুন",welcome:"আপনার ডেস্কটপে স্বাগতম।",status:"প্রদর্শন ও ইনপুট ভাষা নির্বাচন করুন।"},
    "zh-CN":{button:"语言",title:"语言和输入",display:"显示语言",input:"键盘 / 输入法",apply:"应用语言",custom:"其他 BCP-47 语言标签",voice:"播放语音示例",dictate:"开始听写",close:"关闭",welcome:"欢迎使用桌面。",status:"选择显示语言和输入来源。"},
    ja:{button:"言語",title:"言語と入力",display:"表示言語",input:"キーボード / 入力ソース",apply:"言語を適用",custom:"その他の BCP-47 言語タグ",voice:"音声サンプルを再生",dictate:"音声入力を開始",close:"閉じる",welcome:"デスクトップへようこそ。",status:"表示言語と入力ソースを選択してください。"},
    ko:{button:"언어",title:"언어 및 입력",display:"표시 언어",input:"키보드 / 입력 소스",apply:"언어 적용",custom:"기타 BCP-47 언어 태그",voice:"음성 샘플 재생",dictate:"받아쓰기 시작",close:"닫기",welcome:"데스크톱에 오신 것을 환영합니다.",status:"표시 언어와 입력 소스를 선택하세요."},
    pt:{button:"Idioma",title:"Idioma e entrada",display:"Idioma de exibição",input:"Teclado / fonte de entrada",apply:"Aplicar idioma",custom:"Outra etiqueta BCP-47",voice:"Reproduzir amostra",dictate:"Iniciar ditado",close:"Fechar",welcome:"Boas-vindas à sua área de trabalho.",status:"Escolha o idioma de exibição e de entrada."},
    it:{button:"Lingua",title:"Lingua e input",display:"Lingua di visualizzazione",input:"Tastiera / sorgente di input",apply:"Applica lingua",custom:"Altro tag lingua BCP-47",voice:"Riproduci un esempio",dictate:"Avvia dettatura",close:"Chiudi",welcome:"Benvenuto sul desktop.",status:"Scegli la lingua di visualizzazione e di input."},
    nl:{button:"Taal",title:"Taal en invoer",display:"Weergavetaal",input:"Toetsenbord / invoerbron",apply:"Taal toepassen",custom:"Andere BCP-47-taaltag",voice:"Voorbeeld uitspreken",dictate:"Dicteren starten",close:"Sluiten",welcome:"Welkom op uw bureaublad.",status:"Kies de weergave- en invoertaal."},
    pl:{button:"Język",title:"Język i wprowadzanie",display:"Język wyświetlania",input:"Klawiatura / źródło wprowadzania",apply:"Zastosuj język",custom:"Inny tag języka BCP-47",voice:"Odtwórz próbkę mowy",dictate:"Rozpocznij dyktowanie",close:"Zamknij",welcome:"Witamy na pulpicie.",status:"Wybierz język wyświetlania i wprowadzania."}
  };
  const labels = {
    en:{Applications:"Applications",Settings:"Settings",Files:"Files",Browser:"Browser",Terminal:"Terminal",Search:"Search",Help:"Help",Desktop:"Desktop",Wallpaper:"Wallpaper",Start:"Start"},
    ar:{Applications:"التطبيقات",Settings:"الإعدادات",Files:"الملفات",Browser:"المتصفح",Terminal:"الطرفية",Search:"بحث",Help:"مساعدة",Desktop:"سطح المكتب",Wallpaper:"الخلفية",Start:"ابدأ"},
    fr:{Applications:"Applications",Settings:"Paramètres",Files:"Fichiers",Browser:"Navigateur",Terminal:"Terminal",Search:"Rechercher",Help:"Aide",Desktop:"Bureau",Wallpaper:"Fond d’écran",Start:"Démarrer"},
    de:{Applications:"Anwendungen",Settings:"Einstellungen",Files:"Dateien",Browser:"Browser",Terminal:"Terminal",Search:"Suche",Help:"Hilfe",Desktop:"Desktop",Wallpaper:"Hintergrund",Start:"Start"},
    es:{Applications:"Aplicaciones",Settings:"Ajustes",Files:"Archivos",Browser:"Navegador",Terminal:"Terminal",Search:"Buscar",Help:"Ayuda",Desktop:"Escritorio",Wallpaper:"Fondo",Start:"Inicio"},
    ru:{Applications:"Приложения",Settings:"Настройки",Files:"Файлы",Browser:"Браузер",Terminal:"Терминал",Search:"Поиск",Help:"Справка",Desktop:"Рабочий стол",Wallpaper:"Обои",Start:"Пуск"},
    "zh-CN":{Applications:"应用程序",Settings:"设置",Files:"文件",Browser:"浏览器",Terminal:"终端",Search:"搜索",Help:"帮助",Desktop:"桌面",Wallpaper:"壁纸",Start:"开始"},
    ja:{Applications:"アプリケーション",Settings:"設定",Files:"ファイル",Browser:"ブラウザー",Terminal:"ターミナル",Search:"検索",Help:"ヘルプ",Desktop:"デスクトップ",Wallpaper:"壁紙",Start:"スタート"},
    ko:{Applications:"앱",Settings:"설정",Files:"파일",Browser:"브라우저",Terminal:"터미널",Search:"검색",Help:"도움말",Desktop:"데스크톱",Wallpaper:"배경 화면",Start:"시작"}
  };
  const getStored = (key, fallback) => { try { return localStorage.getItem(key) || fallback; } catch (_) { return fallback; } };
  const store = (key, value) => { try { localStorage.setItem(key, value); } catch (_) {} };
  const normalize = value => { try { return Intl.getCanonicalLocales(String(value).trim())[0] || "en"; } catch (_) { return "en"; } };
  const localeBase = value => normalize(value).split("-")[0].toLowerCase();
  const initialLocale = normalize(getStored("aurora.display-language", navigator.language || "en"));
  const initialInput = getStored("aurora.input-language", "en");
  const style = document.createElement("style");
  style.textContent = "#auroraLanguageButton{position:fixed;top:44px;right:18px;z-index:10001;border:1px solid #ffffff55;border-radius:11px;padding:8px 13px;background:#102943eF;color:#fff;font:600 12px system-ui;cursor:pointer;box-shadow:0 5px 22px #0005}#auroraLanguagePanel{position:fixed;top:88px;right:18px;z-index:10002;width:min(370px,calc(100vw - 36px));max-height:calc(100vh - 110px);overflow:auto;padding:16px;border:1px solid #ffffff55;border-radius:16px;background:#0b203af5;color:#f6fbff;box-shadow:0 18px 70px #0009;backdrop-filter:blur(28px);font:13px system-ui}#auroraLanguagePanel[hidden]{display:none}#auroraLanguagePanel[dir=rtl]{right:auto;left:18px;text-align:right}#auroraLanguagePanel h2{font-size:17px;margin:0 0 14px}#auroraLanguagePanel label{display:block;margin:12px 0 5px;color:#d7e8f5}#auroraLanguagePanel select,#auroraLanguagePanel input{width:100%;min-height:36px;border:1px solid #ffffff3c;border-radius:8px;padding:7px 9px;background:#132f4d;color:#fff;font:inherit}#auroraLanguagePanel .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}#auroraLanguagePanel button{border:1px solid #ffffff40;border-radius:9px;padding:8px 10px;background:#d7f7ff18;color:#fff;font:inherit;cursor:pointer}#auroraLanguagePanel .status{min-height:34px;margin:12px 0 0;color:#bcd2e5;line-height:1.5}html[dir=rtl] body{direction:rtl}html[dir=rtl] .menu,html[dir=rtl] .dock,html[dir=rtl] .topbar{direction:rtl}html[dir=rtl] .right{margin-left:0;margin-right:auto}";
  document.head.append(style);
  const button = document.createElement("button");
  button.id = "auroraLanguageButton"; button.type = "button"; button.setAttribute("aria-expanded","false");
  const panel = document.createElement("section");
  panel.id = "auroraLanguagePanel"; panel.hidden = true; panel.setAttribute("role","dialog"); panel.setAttribute("aria-modal","false");
  panel.innerHTML = '<h2 id="auroraLanguageTitle"></h2><label id="auroraDisplayLabel" for="auroraDisplaySelect"></label><select id="auroraDisplaySelect"></select><label id="auroraCustomLabel" for="auroraCustomLocale"></label><div class="actions"><input id="auroraCustomLocale" type="text" maxlength="64" placeholder="fr-CA" autocomplete="off"><button id="auroraApplyCustom" type="button"></button></div><label id="auroraInputLabel" for="auroraInputSelect"></label><select id="auroraInputSelect"></select><div class="actions"><button id="auroraSpeak" type="button"></button><button id="auroraDictate" type="button"></button><button id="auroraClose" type="button"></button></div><p id="auroraLanguageStatus" class="status" role="status" aria-live="polite"></p>';
  const voiceButton = document.createElement("button");
  voiceButton.id = "auroraVoiceConnectButton";
  voiceButton.type = "button";
  voiceButton.textContent = "VoiceConnect";
  voiceButton.setAttribute("aria-label", "Launch VoiceConnect P2P");
  voiceButton.style.cssText = "position:fixed;top:44px;left:18px;z-index:10001;border:1px solid #ffffff55;border-radius:11px;padding:8px 13px;background:#102943ef;color:#fff;font:600 12px system-ui;cursor:pointer;box-shadow:0 5px 22px #0005";
  voiceButton.addEventListener("click", () => {
    const bridge = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.auroraHost;
    if (bridge) {
      bridge.postMessage(JSON.stringify({type:"launch-app",app:"voiceconnect"}));
      status("Starting the local VoiceConnect interface. Call readiness depends on network and peer connectivity.");
    } else {
      status("VoiceConnect is packaged for the live desktop session; the native launch bridge is unavailable here.");
    }
  });
  document.body.append(button, panel, voiceButton);
  const $ = id => document.getElementById(id);
  const display = $("auroraDisplaySelect"), input = $("auroraInputSelect");
  languages.forEach(([tag,name,layout]) => {
    const a = document.createElement("option"); a.value=tag; a.textContent=name; display.append(a);
    const b = document.createElement("option"); b.value=tag; b.textContent=name; b.dataset.layout=layout; input.append(b);
  });
  const translateSimpleLabels = locale => {
    const map = labels[localeBase(locale)] || labels.en;
    document.querySelectorAll("button,a,span,h1,h2,h3,label").forEach(node => {
      if (node.closest("#auroraLanguagePanel") || node.id === "auroraLanguageButton") return;
      if (node.childElementCount !== 0 || node.childNodes.length !== 1 || node.childNodes[0].nodeType !== Node.TEXT_NODE) return;
      const original = node.dataset.auroraOriginalText || node.textContent.trim();
      if (Object.prototype.hasOwnProperty.call(map, original)) {
        node.dataset.auroraOriginalText = original;
        node.textContent = map[original];
      } else if (node.dataset.auroraOriginalText) node.textContent = node.dataset.auroraOriginalText;
    });
  };
  const applyLocale = value => {
    const locale = normalize(value), base = localeBase(locale), strings = copy[base] || copy.en;
    document.documentElement.lang = locale;
    document.documentElement.dir = rtl.has(base) ? "rtl" : "ltr";
    document.body.dir = document.documentElement.dir;
    display.value = languages.some(x => x[0].toLowerCase() === locale.toLowerCase()) ? locale : "";
    button.textContent = strings.button;
    $("auroraLanguageTitle").textContent = strings.title;
    $("auroraDisplayLabel").textContent = strings.display;
    $("auroraInputLabel").textContent = strings.input;
    $("auroraCustomLabel").textContent = strings.custom;
    $("auroraApplyCustom").textContent = strings.apply;
    $("auroraSpeak").textContent = strings.voice;
    $("auroraDictate").textContent = strings.dictate;
    $("auroraClose").textContent = strings.close;
    translateSimpleLabels(locale);
    store("aurora.display-language", locale);
    window.dispatchEvent(new CustomEvent("aurora-locale-change",{detail:{locale,direction:document.documentElement.dir}}));
    return locale;
  };
  const status = value => { $("auroraLanguageStatus").textContent = value; };
  button.addEventListener("click", () => {
    panel.hidden = !panel.hidden; button.setAttribute("aria-expanded",String(!panel.hidden));
    panel.dir = document.documentElement.dir;
    if (!panel.hidden) display.focus();
  });
  $("auroraClose").addEventListener("click", () => { panel.hidden=true; button.setAttribute("aria-expanded","false"); button.focus(); });
  display.addEventListener("change", () => { const locale=applyLocale(display.value); status((copy[localeBase(locale)]||copy.en).status); });
  $("auroraApplyCustom").addEventListener("click", () => {
    const raw=$("auroraCustomLocale").value.trim();
    if (!raw) { status("Enter a BCP-47 language tag, for example fr-CA or ar-JO."); return; }
    try { const locale=applyLocale(raw); $("auroraCustomLocale").value=locale; status("Display language set to "+locale+". Untranslated resources use the configured fallback."); }
    catch (_) { status("Invalid BCP-47 language tag."); }
  });
  input.value = languages.some(x=>x[0]===initialInput) ? initialInput : "en";
  input.addEventListener("change", () => {
    const selected=languages.find(x=>x[0]===input.value);
    if (!selected) return;
    store("aurora.input-language",selected[0]);
    const bridge=window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.auroraHost;
    if (bridge) {
      bridge.postMessage(JSON.stringify({type:"set-input-layout",locale:selected[0],layout:selected[2]}));
      status("Requested "+selected[1]+" keyboard layout from the desktop host. IME support depends on installed input-method providers.");
    } else {
      status("Saved "+selected[1]+" input preference. Native keyboard layout switching requires the live desktop host.");
    }
    window.dispatchEvent(new CustomEvent("aurora-input-language-change",{detail:{locale:selected[0],layout:selected[2]}}));
  });
  $("auroraSpeak").addEventListener("click", () => {
    if (!("speechSynthesis" in window) || !window.SpeechSynthesisUtterance) { status("Speech output is unavailable in this browser/runtime."); return; }
    const locale=normalize(getStored("aurora.display-language","en")), phrase=(copy[localeBase(locale)]||copy.en).welcome;
    const utterance=new SpeechSynthesisUtterance(phrase); utterance.lang=locale;
    const voices=window.speechSynthesis.getVoices();
    const voice=voices.find(v=>v.lang.toLowerCase()===locale.toLowerCase())||voices.find(v=>v.lang.toLowerCase().startsWith(localeBase(locale)+"-"));
    if (voice) utterance.voice=voice;
    utterance.onerror=()=>status("No usable speech voice is installed for "+locale+".");
    utterance.onstart=()=>status("Speaking in "+locale+".");
    utterance.onend=()=>status("Speech sample finished.");
    window.speechSynthesis.cancel(); window.speechSynthesis.speak(utterance);
  });
  $("auroraDictate").addEventListener("click", () => {
    const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
    if (!Recognition) { status("Speech recognition is not exposed by this browser/runtime. Install a compatible speech provider or use keyboard input."); return; }
    const locale=normalize(getStored("aurora.display-language","en")), recognition=new Recognition();
    recognition.lang=locale; recognition.interimResults=false; recognition.maxAlternatives=1;
    recognition.onresult=event=>{
      const text=event.results?.[0]?.[0]?.transcript||"";
      const target=document.activeElement;
      if (target && (target.tagName==="INPUT"||target.tagName==="TEXTAREA") && !target.readOnly && !target.disabled) {
        const start=target.selectionStart??target.value.length, end=target.selectionEnd??start;
        target.setRangeText(text,start,end,"end"); target.dispatchEvent(new Event("input",{bubbles:true}));
      } else document.dispatchEvent(new CustomEvent("aurora-dictation",{detail:{text,locale}}));
      status(text ? "Recognized: "+text : "No speech was recognized.");
    };
    recognition.onerror=event=>status("Speech recognition unavailable: "+event.error);
    recognition.onend=()=>{ if (!$("auroraLanguageStatus").textContent.startsWith("Recognized:")) status("Dictation ended."); };
    try { recognition.start(); status("Listening for "+locale+"."); } catch (error) { status("Could not start dictation: "+error.message); }
  });
  applyLocale(initialLocale);
  status((copy[localeBase(initialLocale)]||copy.en).status);
  window.AuroraI18n = {setLocale:applyLocale,getLocale:()=>normalize(getStored("aurora.display-language","en")),supportedLocales:languages.map(x=>x[0])};
})();