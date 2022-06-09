# Autore: zhao luca
# Data: 11 giugno
# Oggetto: creazione di una funzione che è ingrado di valutare la rilevanza di una lista di
#       url in base alle parole chiavi.
#
#       La funzione restituisce una lista [che contiene le mini-liste che contengono da
#       una parte url passata, dall'altra una valutazione in stringa generata dal metodo
#       di valutazione "ad ascii" (penso che sia mio metodo originale! :D )] ordinata in base
#       alla rilevanza delle url alle parole chiavi passate relativa ad altre url
#
# Criteria valutazione di Metodo Ascii:
# (La tabella di codice può essere cambiata in una qualsiasi, ameno che non superi
#  i bit di integer)
#       La valutazione di un sito è in base alle parole chiavi che contiene:
#       Siccome le parole chiavi sono in una lista, ogni parola chiave corrisponde ad un index
#       e con index, aggiungendo un valore di offset (io metto 64), e avrà una corrispondenza
#       con caratteri di tabella codice ascii:
#               offset=64: index0=(offset+0)='@', index1='A', index20='T'...
#
#       Poi in base a "ha la parola chiave" o meno del url, viene aggiunto alla stringa di
#       valutazione di url il carattere corrispondente. Se una url non contiene nessuna parola chiave
#       allora viene aggiunto il carattere che corrisponde al valore num: (offset-1).
#
#       La funzione restituisce una lista delle mini-liste che contengono index0, url e index1, stringa val.
#       Tale stringa di valutazione è ordinata in modo tale che la url più rilevante è in cima.
#
#       Le parole chiavi che contiene una url possono essere poi ricavate con una operazione riversa, facendo
#       matching dei caratteri di stringa, i valore numerico, con index di parole chiavi nella lista.
#
#   v2.0: (14.giugno)
#       -rinominato la funzione url_has_token in relevance_of
#       -rinominato la funzione urls_have_tokens in evaluate_urls
#       -incorporare la funzione
#       -controllo di più parole chiavi alla volta per ridurre numero di richieste
#       -sistema di valutazione in percentuale: la prima parola chiave ha una percentuale prestabilita e
#        la percentuale di altre parole chiavi dimezza man mano si sposta
#        es: %primo=60, %secondo=(100-60)/2, %terzo=(100-60)/4... %ultimo=2*( (100-60)/index )
#
#   v3.0: (14.giugno)
#       -eliminazione dell'opzione printProcess per aumentare la leggibilità del codice
try:
    from selenium import webdriver
    from bs4 import BeautifulSoup
    import cloudscraper
except ImportError:
    print("Requested modules not installed")

#La funzione relevance_of_url prende i seguenti parametri:
#   -str url: url da analizzare
#
#   -list[str] keywords: tutte le parole chiavi da cercare,
#       la priorità di ogni parola scende a crescere di indice
#
#   -float first_percentage: la priorità in percentuale di
#       prima parola chiave
#
#E restituisce:
#   -float relevance: valore in percentuale di rilevanza della URL passata
def relevance_of_url(url, keywords, first_percentage=60):
    # valore di rilevanza
    qty_keys = len(keywords)
    relevance = 0  # rilevanza in percentuale di url alle parole chiavi

#[STEP 1]: ACQUISIZIONE DI URL INTERNE DA ANALIZZARE
    # usare cloudscraper per inviare richiesta http
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    })
    req = scraper.get(url)
    soup = BeautifulSoup(req.content, "html.parser")

    # determinare se funziona con cloudscraper, sennò passa al metodo di webdriver
    if soup.find("a") is None:
        # Usare metodo di webdriver per scraping
        # setup di opzioni
        options = webdriver.ChromeOptions()
        options.add_argument('--incognito')
        options.add_argument('--headless')
        # accesso alla url con chromedriver
        driver = webdriver.Chrome(executable_path="C:\\Users\\xizh0\\Documents\\chromedriver.exe", options=options)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")

    # raw_refs contiene tutti i href del url (non tutti i rami
    # del sito web)
    raw_refs = soup.find_all("a")
    # internal_refs contiene solo riferimenti interni e ripuliti ad
    # ottenere solo gli url
    internal_refs = []

    # filtraggio di hrefs per ottenere solo url di href interne
    for raw_ref in raw_refs:
        ref_str = str(raw_ref.get("href"))
        # Se è path relativo della pagina. In tal caso viene
        # appeso alla url il path relativo
        if "http://" not in ref_str and "https://" not in ref_str:
            # Se il path relativo è il nonno di url
            if "../../" in ref_str:
                # eliminare l'ultimo file e l'ultimo dir (es .../dir/subdir/file1.html => .../dir)
                last_index = url.rfind("/")
                last_index = url[:last_index].rfind("/")
                last_index = url[:last_index].rfind("/")
                last_index = url[:last_index].rfind("/")
                ref_str = url[:last_index + 1] + ref_str.replace("../..", "", 1)
            # Se il path relativo è il genitore di url
            elif "../" in ref_str:
                # eliminare l'ultimo file e l'ultimo dir (es .../dir/subdir/file1.html => .../dir)
                last_index = url.rfind("/")
                ref_str = url[:last_index + 1] + ref_str.replace("../", "", 1)
            # Se il path relativo è il sibling di url
            elif "./" in ref_str:
                # eliminare l'ultimo file e l'ultimo dir (es .../dir/subdir/file1.html => .../dir)
                last_index = url.rfind("/")
                ref_str = url[:last_index + 1] + ref_str.replace("./", "", 1)
                print(ref_str)
            else:
                # eliminare l'ultimo file (es .../dir/file1.html => .../dir)
                last_index = url.rfind("/")
                ref_str = url[:last_index + 1] + ref_str

        # escludere i link che contengono multimedia file
        multimedia_extensions = ['.jpg', '.jpeg', '.mpg', '.png', '.mp4',
                                '.mp3', '.wmv', '.avi', '.flv', '.mov','.pdf', 'tel:', 'mailto:']
        is_multimedia = False
        i = 0
        while i < len(multimedia_extensions) and not is_multimedia:
            if multimedia_extensions[i] in ref_str.strip():
                is_multimedia = True
            i += 1

        # aggiungere alla lista la url se non è multimedia e se il riferimento è una url
        if not is_multimedia and url in ref_str:
            internal_refs.append(ref_str)

    # aggiungere se stesso alla lista per essere valutato
    internal_refs.append(url)

    # cancellare le url ripetute
    internal_refs = list(dict.fromkeys(internal_refs))

    # iterare per tutte le pagine interne per controllare se il sito contiene
    # la parola chiava. Nel caso di prelievo restituisce True, altrimenti False.
    # Questo è ancora un demo, quindi restituisce un valore booleano. Scriverò
    # la funzione che contiene un sistema di valutazione.

#[STEP 2]: ANALIZZARE TUTTE LE URL
    #iterare per tutte le parole chiavi, su tutte le href interne.
    keys = list.copy(keywords)
    i = 0
    while i < len(internal_refs) and len(keys) > 0:
        #usare cloudscraper per inviare richiesta http
        scraper = cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        })
        req = scraper.get(internal_refs[i])
        soup = BeautifulSoup(req.content, "html.parser")

        # determinare se funziona con cloudscraper, sennò passa al metodo di webdriver
        if soup.find(['p','h']) is None:
            # Usare metodo di webdriver per scraping
            # setup di opzioni
            options = webdriver.ChromeOptions()
            options.add_argument('--incognito')
            options.add_argument('--headless')
            # accesso alla url con chromedriver
            driver = webdriver.Chrome(executable_path="C:\\Users\\xizh0\\Documents\\chromedriver.exe", options=options)
            driver.get(internal_refs[i])
            soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract i paragrafi
        paragraphs = soup.find_all(['p', 'h'])

        # STAMPA PROCESSO

        # iterare tutti i paragrafi per valutare la rilevanza
        k = 0
        while k < len(paragraphs) and len(keys) > 0:
            #iterare tutte le parole chiavi per stabilire se contiene o meno
            j = 0
            while j < len(keys):
                # ricerca di parola chiave
                if keys[j].lower() in paragraphs[k].text.lower():
                    # stabilire valore di parolachiave in base alla sua index
                    if qty_keys > 1:  # se la quantità di parola vhiace è maggiore di 1
                        index = keywords.index(keys[j])
                        if index == 0:  # se è la prima parola chiav
                            relevance += first_percentage
                        elif index == qty_keys - 1:
                            relevance += (100 - first_percentage) / (2 * (index)) * 2
                        else:
                            relevance += (100 - first_percentage) / (2 * (index))

                    else:  # se c'è solo una parola chiave e si trova allora restituisce subito 100
                        return 100.0

                    keys.remove(keys[j])
                #cambio di parola chiave
                j += 1
            #cambio di paragrafo
            k += 1
        #cambio di url
        i += 1

    # restituzione di rilevanza
    return relevance

print(relevance_of_url("https://www.stannah.it",["montascale","aoo"],80))