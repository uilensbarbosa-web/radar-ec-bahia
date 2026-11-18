const ESCUDO_OFICIAL = "https://i.ibb.co/P3wjSMc/Escudo-Bahia-848x1024.webp";

let movimentacoesBahia = [];
let filtroTipo = "TODOS";
let termoBusca = "";

const container = document.getElementById("cardsContainer");
const statusBar = document.getElementById("statusBar");

function criarEscudoCirculo() {
    return `<div style="width:44px; height:44px; border-radius:50%; background:#ffffff; border:2px solid #ffffff; display:flex; align-items:center; justify-content:center; box-shadow:0 3px 8px rgba(0,0,0,0.4); overflow:hidden; padding:4px;">
        <img src="${ESCUDO_OFICIAL}" alt="EC Bahia" style="width:100%; height:100%; object-fit:contain;">
    </div>`;
}

function classificarMovimentacao(texto) {
    const t = texto.toLowerCase();
    if (t.includes("renova") || t.includes("renovação") || t.includes("novo contrato") || t.includes("estende") || t.includes("amplia vínculo")) {
        return { tipo: "RENOVACAO", label: "✍️ Renovação", cor: "#1e3a8a", direcao: "IN" };
    }
    if (t.includes("saída") || t.includes("deixa o") || t.includes("sai do") || t.includes("rescinde") || t.includes("rescisão") || t.includes("empréstimo do") || t.includes("empresta") || t.includes("emprestado") || t.includes("vendido") || t.includes("venda") || t.includes("despede") || t.includes("dispensa")) {
        return { tipo: "SAIDA", label: "📤 Saída / Empréstimo", cor: "#991b1b", direcao: "OUT" };
    }
    return { tipo: "CHEGADA", label: "📥 Chegada / Rumor", cor: "#005ca9", direcao: "IN" };
}

async function buscarNoticiasBahia() {
    statusBar.innerText = "🔍 Carregando movimentações do Esporte Clube Bahia...";
    container.innerHTML = "";

    try {
        const resp = await fetch("/api/noticias");

        const dados = await resp.json();

        movimentacoesBahia = dados.map((item, index) => {
            const info = classificarMovimentacao(item.titulo);
            return {
                id: index + 1,
                titulo: item.titulo,
                fonte: item.fonte,
                data: item.data || "2026",
                tipo: info.tipo,
                labelTipo: info.label,
                corCard: info.cor,
                direcao: info.direcao,
                linkOriginal: item.link
            };
        });

        statusBar.innerText = `🔵🔴⚪ ${movimentacoesBahia.length} movimentações do Esporte Clube Bahia carregadas.`;
        renderizarCards();
    } catch (erro) {
        statusBar.innerText = "⚠️ Inicie o app.py da pasta RadarBahia no VS Code.";
    }
}
function renderizarCards() {
    container.innerHTML = "";
    const filtrados = movimentacoesBahia.filter(item => {
        const bateTipo = filtroTipo === "TODOS" || item.tipo === filtroTipo;
        const bateBusca = `${item.titulo} ${item.fonte} ${item.data}`.toLowerCase().includes(termoBusca.toLowerCase());
        return bateTipo && bateBusca;
    });

    if (filtrados.length === 0) {
        container.innerHTML = `<p style="color:#aaa; grid-column: 1/-1; text-align:center; padding: 40px;">Nenhuma movimentação encontrada para este filtro.</p>`;
        return;
    }

    const estiloCirculo = "width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:0.95rem; border:2px solid #fff; box-shadow:0 3px 8px rgba(0,0,0,0.4);";
    const escudoCard = criarEscudoCirculo();

    filtrados.forEach(item => {
        const origem = item.direcao === "OUT"
            ? escudoCard
            : `<div style="${estiloCirculo} background:#0f172a; color:#fff;">⚽</div>`;

        const destino = item.direcao === "OUT"
            ? `<div style="${estiloCirculo} background:#0f172a; color:#fff;">✈️</div>`
            : escudoCard;

        const card = document.createElement("div");
        card.className = "transfer-card";
        card.style.backgroundColor = item.corCard;
        card.style.color = "#FFFFFF";
        card.innerHTML = `
            <div>
                <div class="card-visual-header" style="height: 92px; margin-bottom: -20px; position: relative; overflow: hidden;">
                    <img src="${ESCUDO_OFICIAL}" alt="" style="position: absolute; right: 12px; top: -8px; height: 110px; opacity: 0.16; pointer-events: none;">
                    <div class="club-banner-text" style="font-size: 1.4rem; position: relative; z-index: 2;">EC BAHIA</div>
                </div>
                <div class="transfer-flow">
                    <div class="clubs-transition">
                        ${origem}
                        <span class="arrows">»»»</span>
                        ${destino}
                    </div>
                    <span class="division-tag" style="font-size: 0.78rem; padding: 5px 10px; background: rgba(0,0,0,0.35);">${item.labelTipo}</span>
                </div>
                <div class="player-info-row" style="margin-top: 12px;">
                    <a href="${item.linkOriginal}" target="_blank" style="color: inherit; text-decoration: none;">
                        <div class="headline-title" style="font-size: 1.15rem; line-height: 1.4;">${item.titulo}</div>
                    </a>
                    <div class="source-meta" style="margin-top: 10px;">Fonte: ${item.fonte} • 📅 ${item.data}</div>
                </div>
            </div>
            <div class="card-footer" style="margin-top: 18px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.15);">
                <a href="${item.linkOriginal}" target="_blank" class="btn-saiba-mais" style="text-decoration: none;">
                    Ler notícia completa ↗
                </a>
                <div class="reaction-buttons">
                    <button class="react-btn react-dislike" onclick="reagir(this)" title="Não curti">👎</button>
                    <button class="react-btn react-like" onclick="reagir(this)" title="Curti">👍</button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

document.querySelectorAll("#typeFilters .filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll("#typeFilters .filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        filtroTipo = btn.dataset.tipo;
        renderizarCards();
    });
});

document.getElementById("searchInput").addEventListener("input", e => {
    termoBusca = e.target.value;
    renderizarCards();
});

function reagir(btn) {
    btn.style.transform = "scale(1.25)";
    setTimeout(() => btn.style.transform = "scale(1)", 200);
}

const commentForm = document.getElementById("commentForm");
const commentsList = document.getElementById("commentsList");

let comentarios = JSON.parse(localStorage.getItem("comentarios_bahia")) || [
    { autor: "Bora Bahêa", data: "Hoje", texto: "Alejo Véliz e Marco Moreno elevaram muito o nível do elenco em 2026! Agora é aguardar esse atacante da Premier League." }
];

function renderizarComentarios() {
    commentsList.innerHTML = "";
    comentarios.forEach(c => {
        const div = document.createElement("div");
        div.className = "comment-item";
        div.innerHTML = `
            <div class="comment-header">
                <strong>${c.autor}</strong>
                <span>${c.data}</span>
            </div>
            <div class="comment-body">${c.texto}</div>
        `;
        commentsList.appendChild(div);
    });
}

commentForm.addEventListener("submit", e => {
    e.preventDefault();
    const autor = document.getElementById("commentAuthor").value.trim();
    const texto = document.getElementById("commentText").value.trim();
    if (!autor || !texto) return;

    const agora = new Date().toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
    comentarios.unshift({ autor, data: agora, texto });
    localStorage.setItem("comentarios_bahia", JSON.stringify(comentarios));

    document.getElementById("commentText").value = "";
    renderizarComentarios();
});

renderizarComentarios();
buscarNoticiasBahia();
