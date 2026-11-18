import os
import http.server
import socketserver
import urllib.request
import re
import html
import ssl
import time
from concurrent.futures import ThreadPoolExecutor

PORT = int(os.environ.get("PORT", 8090))
CACHE_DADOS = None
CACHE_TEMPO = 0

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def baixar(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    })
    with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
        dados = resp.read()
        try:
            return dados.decode("utf-8")
        except UnicodeDecodeError:
            return dados.decode("latin-1", errors="ignore")

def limpar(t):
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace('"', "'").replace("\n", " ")
    return re.sub(r"\s+", " ", t).strip()

HISTORICO_TEMPORADA = [
    {"titulo": "Bahia estende vínculo contratual de titulares do elenco principal até 2028", "fonte": "GE Bahia", "data": "Out/2026", "ordem": 20261015, "link": "https://globo.com"},
    {"titulo": "Bahia renova contrato de joias da base dos Pivetes de Aço com multa milionária", "fonte": "EC Bahia Oficial", "data": "Set/2026", "ordem": 20260920, "link": "https://ecbahia.com"},
    {"titulo": "Base: Bahia empresta o atacante Caio Suassuna (Sub-20) ao Avaí para disputa da Série B", "fonte": "Pivetes de Aço", "data": "Ago/2026", "ordem": 20260810, "link": "https://ecbahia.com"},
    {"titulo": "Zagueiro Gabriel Xavier deixa o Bahia após transferência acertada pelo clube", "fonte": "EC Bahia Oficial", "data": "Jul/2026", "ordem": 20260718, "link": "https://ecbahia.com"},
    {"titulo": "Bahia confirma saída do zagueiro argentino Ramos Mingo em negociação definitiva", "fonte": "EC Bahia Oficial", "data": "Jul/2026", "ordem": 20260712, "link": "https://ecbahia.com"},
    {"titulo": "Bahia acerta empréstimo do meia Cauly ao São Paulo até o fim da temporada", "fonte": "GE Bahia", "data": "Fev/2026", "ordem": 20260215, "link": "https://globo.com"},
    {"titulo": "Bahia anuncia zagueiro espanhol Marco Moreno como reforço vindo do futebol europeu", "fonte": "EC Bahia Oficial", "data": "Jan/2026", "ordem": 20260122, "link": "https://ecbahia.com"},
    {"titulo": "Bahia oficializa contratação do atacante argentino Alejo Véliz para a temporada", "fonte": "EC Bahia Oficial", "data": "Jan/2026", "ordem": 20260114, "link": "https://ecbahia.com"}
]

def buscar_fonte(args):
    nome_fonte, url, dominio = args
    encontrados = []
    identidade = ["bahia", "esquadrão", "tricolor de aço", "rogério ceni", "cadu santoro", "pivetes", "sub-20"]
    acoes = [
        "interesse", "interessa", "sondagem", "negocia", "proposta", "contrata", "contratação",
        "reforço", "reforços", "acerta", "assina", "empréstimo", "empresta", "emprestado", "rescinde",
        "deixa o", "saída", "sai do", "chega ao", "alvo", "monitora", "encaminha", "fechado",
        "anuncia", "renovação", "renova", "estende", "novo contrato", "dispensa", "compra",
        "venda", "retorno", "volta ao", "vínculo", "abre conversas", "oficializa", "cedido"
    ]
    bloqueios = [
        "árbitro", "escalação", "onde assistir", "ao vivo", "palpite", "ingressos", "tabela",
        "lula", "gols de", "recuperação judicial", "patrocínio", "aeroporto", "novela", "justiça",
        "elogia", "coletiva", "treino", "relacionados", "desfalque", "lesão", "feminino", "basquete",
        "feirão", "dívida", "saf", "aporte", "ronaldinho"
    ]
    try:
        conteudo = baixar(url)
        
        # 1. Se for feed RSS (Google News), extrai os <item> XML
        if "<item>" in conteudo:
            for item in re.findall(r"<item>(.*?)</item>", conteudo, flags=re.DOTALL):
                tm = re.findall(r"<title>(.*?)</title>", item, flags=re.DOTALL)
                lm = re.findall(r"<link>(.*?)</link>", item, flags=re.DOTALL)
                titulo_raw = limpar(next(iter(tm), ""))
                link_full = limpar(next(iter(lm), "#"))
                
                fonte_item = nome_fonte
                if " - " in titulo_raw:
                    partes = titulo_raw.split(" - ")
                    fonte_item = partes.pop()
                    titulo_raw = " - ".join(partes)
                    
                low = titulo_raw.lower()
                if any(i in low for i in identidade) and any(a in low for a in acoes) and not any(b in low for b in bloqueios):
                    encontrados.append({
                        "titulo": titulo_raw,
                        "fonte": fonte_item,
                        "data": "Nov/2026",
                        "ordem": 20261118,
                        "link": link_full
                    })
            return encontrados

        # 2. Se for pagina HTML normal
        candidatos = re.findall(r'<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', conteudo, flags=re.DOTALL | re.IGNORECASE)
        for href, texto in candidatos:
            if href.startswith("javascript") or href.startswith("mailto"):
                continue
            link_full = href if href.startswith("http") else dominio + ("" if href.startswith("/") else "/") + href
            if link_full.rstrip("/") in ["https://ecbahia.com", "https://ecbahia.com/mercado-da-bola", "https://globo.com"]:
                continue

            titulo = re.sub(r"^\d+\s+", "", limpar(texto))
            if len(titulo) < 26 or len(titulo) > 160:
                continue
            low = titulo.lower()
            url_low = link_full.lower()
            eh_bahia = any(i in low for i in identidade) or ("ecbahia.com" in url_low or "infobahea.com" in url_low)
            if eh_bahia and any(a in low for a in acoes) and not any(b in low for b in bloqueios):
                data_match = re.search(r'/(202\d)/(\d{2})/(\d{2})/', link_full)
                if data_match:
                    ano, mes, dia = data_match.group(1), data_match.group(2), data_match.group(3)
                    data_str = f"{dia}/{mes}/{ano}"
                    ordem_num = int(f"{ano}{mes}{dia}")
                else:
                    data_str = "Nov/2026"
                    ordem_num = 20261118
                encontrados.append({
                    "titulo": titulo,
                    "fonte": nome_fonte,
                    "data": data_str,
                    "ordem": ordem_num,
                    "link": link_full
                })
    except Exception:
        pass
    return encontrados

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global CACHE_DADOS, CACHE_TEMPO
        if self.path != "/api/noticias":
            return super().do_GET()

        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        if CACHE_DADOS and (time.time() - CACHE_TEMPO < 600):
            self.wfile.write(CACHE_DADOS.encode("utf-8"))
            return

                portais = [
            # Setoristas e perfis específicos do Bahia no X
            ("X • Setoristas Tricolores", "https://google.com", ""),
            ("X • Venê & Mercado BA", "https://google.com", ""),
            ("X • Busca Geral Bahia", "https://google.com", ""),

            # Portais e Google News tradicional
            ("Google News Bahia", "https://google.com", ""),
            ("Google News Esquadrão", "https://google.com", ""),
            ("ECBahia.com", "https://ecbahia.com", "https://ecbahia.com"),
            ("ECBahia.com", "https://ecbahia.com/page/2", "https://ecbahia.com"),
            ("ECBahia Base", "https://ecbahia.com/base", "https://ecbahia.com"),
            ("Bahia Notícias", "https://bahianoticias.com.br", "https://bahianoticias.com.br"),
            ("Info Bahêa", "https://infobahea.com", "https://infobahea.com"),
            ("NE45 Bahia", "https://ne45.com.br", "https://ne45.com.br"),
            ("GE Bahia", "https://globo.com", "https://globo.com")
        ]


        vistos = set()
        lista_final = []

        with ThreadPoolExecutor(max_workers=7) as executor:
            resultados = executor.map(buscar_fonte, portais)
            for grupo in resultados:
                for item in grupo:
                    if item["titulo"] not in vistos:
                        vistos.add(item["titulo"])
                        lista_final.append(item)

        for hist in HISTORICO_TEMPORADA:
            if hist["titulo"] not in vistos:
                vistos.add(hist["titulo"])
                lista_final.append(hist)

        lista_final.sort(key=lambda x: x["ordem"], reverse=True)

        itens_json = []
        for x in lista_final:
            t = x["titulo"].replace('"', "'")
            f = x["fonte"].replace('"', "'")
            d = x["data"].replace('"', "'")
            l = x["link"].replace('"', "'")
            o = x["ordem"]
            itens_json.append(f'{{"titulo":"{t}","fonte":"{f}","data":"{d}","ordem":{o},"link":"{l}"}}')

        CACHE_DADOS = "[" + ",".join(itens_json) + "]"
        CACHE_TEMPO = time.time()
        self.wfile.write(CACHE_DADOS.encode("utf-8"))

socketserver.TCPServer.allow_reuse_address = True
print(f"Radar EC Bahia ativo na porta {PORT}", flush=True)
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
