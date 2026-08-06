# 📋 Instruções para Kamylla — Exportar Relatórios SGE da Soul Festas

> **Objetivo:** Baixar os relatórios do SGE que alimentam o dashboard financeiro da Soul.
> **Frequência:** Uma vez por mês (antes das reuniões da Laysa com a Soul).
> **Tempo estimado:** 15-20 minutos.
> **Site que será atualizado:** https://soul-finance.streamlit.app/

---

## 🔐 PASSO 1 — Acessar o SGE

Login no SGE da Soul (usar credenciais que já estão configuradas no navegador da Laysa).

---

## 📁 PASSO 2 — Criar a pasta de destino

Antes de baixar qualquer coisa, criar uma pasta nova com a data de HOJE:

**Caminho:**
```
C:\Users\Laysa\Claude_Projetos\soul-festas-dashboard\ingest\data_raw\
```

**Criar subpasta com o formato:** `DD.MM.AAAA` (exemplo: `16.06.2026`)

**Todos os arquivos baixados devem ir para essa pasta.**

---

## 📥 PASSO 3 — Exportar os 7 relatórios

Para todos os relatórios abaixo: **sempre exportar em Excel (.xlsx)** e salvar na pasta criada.

### RELATÓRIO 1 — Contas a Pagar (SÃO 4 ARQUIVOS!)

O SGE só exporta contas a pagar por SEMESTRE, então precisamos baixar 4 vezes:

**Menu:** Financeiro → Contas a Pagar

**Filtros a aplicar (repetir 4 vezes, mudando as datas):**

| Arquivo | Data de | Data até | Nome do arquivo |
|---|---|---|---|
| 1 | 01/01/2025 | 30/06/2025 | `1 SEM 2025 - Contas_a_Pagar...` |
| 2 | 01/07/2025 | 31/12/2025 | `2 SEM 2025 - Contas_a_Pagar...` |
| 3 | 01/01/2026 | 30/06/2026 | `1 SEM 2026 - Contas_a_Pagar...` |
| 4 | 01/07/2026 | 31/12/2026 | `2 SEM 2026 - Contas_a_Pagar...` |

**Status:** deixar "Pagas e Não Pagas" (para trazer tudo)

---

### RELATÓRIO 2 — Contas a Receber PAGAS (SÃO 2 ARQUIVOS!)

**Menu:** Financeiro → Contas a Receber

**Filtro Status da Fatura:** selecionar **"Pagas"**

| Arquivo | Data de Pagamento de | Data de Pagamento até | Nome |
|---|---|---|---|
| 1 | 01/01/2025 | 31/12/2025 | `2025 - Contas a Receber...` |
| 2 | 01/01/2026 | 31/12/2026 | `2026 - Contas a Receber...` |

---

### RELATÓRIO 3 — Contas a Receber NÃO PAGAS (parcelas em aberto)

**Menu:** Financeiro → Contas a Receber (mesma tela do relatório 2)

**Filtros:**
- **Status da Fatura:** selecionar **"Não Pagas"**
- **Data de Vencimento:** DEIXAR AMBAS EM BRANCO (ou colocar 01/01/2025 até 31/12/2027)
- **Data de Pagamento:** DEIXAR EM BRANCO
- **Data de Crédito:** DEIXAR EM BRANCO

⚠️ **IMPORTANTE:** Se limitar a data de vencimento a "hoje", só virão as vencidas (perdemos as parcelas futuras que alimentam a projeção de caixa). O certo é range amplo.

**Nome sugerido:** `Contas nao recebidas_AAAAMMDD.xlsx`

---

### RELATÓRIO 4 — Agenda Resumida

**Menu:** procurar por "Agenda" ou "AgendaResumida"

**Filtros:** trazer todos os eventos de 2025 e 2026 (range amplo)

**Nome:** `AgendaResumida_AAAAMMDD_XXXXX_XXXXX.xlsx`

---

### RELATÓRIO 5 — Balanço Por Projeto Resumido

**Menu:** Relatórios → Balanço Por Projeto (ou nome parecido)

**Filtros:** todos os projetos, sem filtro de data (traz tudo)

**Nome:** `BalancoPorProjetoResumido_AAAAMMDD_XXXXX.xlsx`

---

### RELATÓRIO 6 — Custo Do Projeto

**Menu:** Relatórios → Custo Do Projeto

**Filtros:** todos os projetos

**Nome:** `CustoDoProjeto_AAAAMMDD_XXXXX.xlsx`

---

### RELATÓRIO 7 — Planilha Clientes Inadimplentes

**Menu:** Financeiro → **Cobrança** (submenu) → procurar "Planilha de Clientes Inadimplentes" ou "Inadimplentes"

⚠️ Esta planilha é a **base LIMPA de inadimplentes** (já sem cancelados que a Letícia removeu). É a mais precisa para a aba de Inadimplência do dashboard.

**Nome:** `PlanilhaClientesInadimplentes_AAAAMMDD_XXXXX_XXXXX.xlsx`

Se não encontrar essa opção, avisar a Laysa (o dashboard funciona com fallback usando o Relatório 3, mas com a Planilha o resultado é melhor).

---

## ✅ PASSO 4 — Conferir se está tudo lá

Depois de baixar tudo, abrir a pasta `DD.MM.AAAA` que você criou e conferir:

- [ ] 4 arquivos de **Contas a Pagar** (1SEM2025, 2SEM2025, 1SEM2026, 2SEM2026)
- [ ] 2 arquivos de **Contas a Receber Pagas** (2025 e 2026)
- [ ] 1 arquivo **Contas não recebidas** (com range amplo)
- [ ] 1 arquivo **AgendaResumida**
- [ ] 1 arquivo **BalancoPorProjetoResumido**
- [ ] 1 arquivo **CustoDoProjeto**
- [ ] 1 arquivo **PlanilhaClientesInadimplentes** (se conseguiu)

**Total esperado: 10-11 arquivos** na pasta

---

## 📢 PASSO 5 — Avisar a Laysa

Mandar mensagem no WhatsApp da Laysa:

> "Oi Laysa! Baixei os relatórios do SGE da Soul. Estão na pasta `[DD.MM.AAAA]` dentro de `soul-festas-dashboard/ingest/data_raw/`. Consegui [X] arquivos. [Se faltou algum: "não encontrei o relatório de Inadimplentes, verificar comigo depois"]"

A Laysa então roda o pipeline técnico (`/soul atualizar`) que combina os arquivos, processa e sobe pra internet. O site atualiza em ~2 minutos.

---

## ❓ Dúvidas comuns

**"Não consegui achar um dos relatórios"**
→ Anota qual foi e avisa a Laysa. Ela ou verifica com o Carlos Henrique (contato Soul) ou ajusta manualmente.

**"Baixei mais de uma vez o mesmo arquivo"**
→ Sem problema, deixa todos na pasta. O sistema pega o mais recente pela data do arquivo.

**"O SGE deu erro na exportação"**
→ Espera 2 min e tenta de novo. Se persistir, avisa a Laysa.

**"Não sei qual pasta criar"**
→ Sempre `DD.MM.AAAA` (dia.mês.ano) dentro de `soul-festas-dashboard/ingest/data_raw/`. Ex: hoje = `16.06.2026`.

---

📅 Última atualização deste guia: 16/06/2026
