# SBS Course Comparison (pilot)

En enkel, självständig webbtjänst för **preliminära** jämförelser mellan en kurs vid ett utländskt universitet och **endast studentens tidigare lästa kurser** som finns i SBS:s referensbank. Ingen inloggning eller studerandedatabas ingår i denna pilot.

## Vad studenten gör

1. Söker och väljer tidigare lästa SBS-kurser i en lista, eller laddar upp en **avidentifierad** TXT-, CSV- eller PDF-lista med kurskoder och bekräftar matchningarna.
2. Laddar upp kursplanen för den planerade utländska kursen (textbaserad PDF).
3. Bekräftar att inga personuppgifter finns i dokumenten.
4. Får en preliminär jämförelse med motiveringar, möjliga överlappningar, skillnader och hänvisning till PDF-sidor.

**Viktigt:** Verktyget gör INGEN kontroll mot andra kursplaner än de studenterna uttryckligen har valt. Om tidigare lästa kurser saknas i SBS:s kursbank kan jämförelsen vara ofullständig. Källhänvisningar och slutsatser måste kontrolleras mot originaldokumenten.

## Publicera utan egen server

### A. Lägg in kursplanerna

1. Packa upp ZIP-filen på din dator.
2. Lägg de **offentliga** kursplanerna från SBS som separata PDF-filer i `course_plans/`. 100 PDF-filer fungerar som filsamling; analysen görs bara av studentens valda kurser. Du behöver inte slå ihop PDF:erna.
3. Namnge helst PDF:erna exempelvis `FE1234_Buyer_Behaviour.pdf`. Det är **bara ett namnexempel**, inte en faktisk verifierad SBS-kurskod.
4. Om filnamnen inte följer mönstret kan du skapa `course_plans/catalog.csv` med kolumnerna `filename,code,title`, enligt `catalog_example.csv`.
5. Lämna inte fiktiva exempelrader i en aktiv `catalog.csv`.

### B. GitHub

1. Skapa ett konto på [github.com](https://github.com).
2. Skapa ett nytt repository, exempelvis `sbs-course-comparison`.
3. Ladda upp innehållet i den uppackade mappen **med mappstrukturen bevarad**: `app.py`, `core.py`, `requirements.txt`, `.streamlit/config.toml`, `course_plans/` och PDF:erna. I GitHub kan du använda **Add file → Upload files**. Om en dold mapp som `.streamlit` inte går att dra in, skapa dess fil via **Add file → Create new file** med filnamnet `.streamlit/config.toml`.
4. Kontrollera att PDF-filerna verkligen är offentliga innan du använder ett publikt GitHub-repository. Ett offentligt repository gör även PDF-filerna offentliga.
5. Lägg ALDRIG in en API-nyckel i GitHub-kod eller PDF:erna.

### C. Google Gemini API

1. Öppna [Google AI Studio → API keys](https://aistudio.google.com/api-keys).
2. Skapa eller kopiera en API-nyckel från ett projekt du har rätt att använda.
3. **Lägg inte in nyckeln i GitHub.** Använd Streamlits *Secrets* enligt nästa steg.
4. Appen använder som standard `gemini-2.5-flash`. Gratisnivån har kvoter och Google anger att innehåll i kostnadsfria API-anrop kan användas för produktförbättring. För studentdrift bör SU först avgöra om den behandlingen är tillåten. Betalnivån har andra villkor.

### D. Streamlit Community Cloud

1. Öppna [share.streamlit.io](https://share.streamlit.io), logga in via GitHub och välj **Create app**.
2. Välj ditt GitHub-repository, branch `main` och filen `app.py`.
3. Öppna **Advanced settings → Secrets** och skriv:

   ```toml
   GEMINI_API_KEY = "DIN_HEMLIGA_NYCKEL"
   APP_ACCESS_CODE = "ETT_LANGT_PILOTLOESENORD"
   ```

   `APP_ACCESS_CODE` är valfri och lämplig endast som ett enkelt skydd för en pilot. **Det är ingen verklig användarautentisering.** För en tjänst till studenter bör SU ta ställning till åtkomstkontroll och drift.
4. Klicka **Deploy**. Du får en webbaddress på `*.streamlit.app`, som kan delas med testanvändare.
5. Testa med ett separat konto och en utländsk provkursplan, sedan med fler kurser.

## Begränsningar och informationssäkerhet

- **Ingen automatisk matchning av alla 100 kurser:** Studenten väljer tidigare lästa kurser. Inmatade kurslistor matchas lokalt mot koder eller exakta titlar, med manuell bekräftelse.
- **Falska positiva och missade överlappningar:** AI-analysen är vägledande. Den har inte testats mot SBS:s verkliga kursplaner ännu.
- **PDF måste innehålla maskinläsbar text:** Skannade dokument utan text stöds inte i piloten.
- **Begränsningar:** Högst 32 valda SBS-kurser, 8 MB utländsk PDF och 30 sidor; analys i grupper om åtta kurser.
- **Ingen databas:** Pilotkoden lagrar inte medvetet uppladdningar eller studentidentiteter. Streamlit och Google är däremot externa personuppgifts-/infrastrukturleverantörer. Applikationens avsaknad av databas innebär **inte** att leverantörerna saknar loggar eller lagring.
- **Dataplacering:** Streamlit Community Cloud anger att deras appar driftas i USA. Detta måste vägas in i SU:s informationssäkerhets- och dataskyddsbedömning.
- **API:s kostnadsfria nivå:** Google anger att data som skickas via gratisnivån kan användas för att förbättra deras produkter. Skicka därför inte studentuppgifter och publicera inte för studenter före relevant godkännande.
- **Kostnad och missbruk:** Gratis drift och gratis API är kvotbegränsade. En publik app med en serverlagrad API-nyckel kan förbruka tilldelad API-kvot. Begränsning per session är inte ett fullgott skydd. Uppföljning/kvoter hos API-leverantören behövs vid riktig drift.
- **Beslut:** Resultatet är aldrig ett formellt godkännande av Learning Agreement eller tillgodoräknande. Hänvisa till SBS:s gällande information.

## Testa lokalt (frivilligt)

```bash
python -m pip install -r requirements.txt
export GEMINI_API_KEY="YOUR_API_KEY"    # Windows PowerShell: $env:GEMINI_API_KEY="YOUR_API_KEY"
streamlit run app.py
```

Koden är en prototyp. API:t har inte provanropats från denna miljö eftersom ingen API-nyckel är tillgänglig. Kontrollera både funktion och informationssäkerhet med verkliga SBS-kursplaner innan lansering.
