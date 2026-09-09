import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def main():
    # Guarantee output folder exists
    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    random.seed(42)
    np.random.seed(42)
    
    print("[+] Gerando dados ficticios para o Dashboard de SLA...")

    # ---------------------------------------------------------
    # 1. CLIENTES (clientes.csv)
    # ---------------------------------------------------------
    clientes_data = [
        {"cliente_id": "CLI-001", "nome_cliente": "TechCorp Soluções (Fictício)", "segmento": "Tecnologia", "horas_contratadas_mes": 120, "valor_hora_adicional": 220.00, "gerente_conta": "Mariana Souza"},
        {"cliente_id": "CLI-002", "nome_cliente": "InovaLog Logística (Fictício)", "segmento": "Logística", "horas_contratadas_mes": 80, "valor_hora_adicional": 200.00, "gerente_conta": "Carlos Andrade"},
        {"cliente_id": "CLI-003", "nome_cliente": "FinanceHub Capital (Fictício)", "segmento": "Finanças", "horas_contratadas_mes": 160, "valor_hora_adicional": 280.00, "gerente_conta": "Mariana Souza"},
        {"cliente_id": "CLI-004", "nome_cliente": "RetailMax Varejo (Fictício)", "segmento": "Varejo", "horas_contratadas_mes": 60, "valor_hora_adicional": 190.00, "gerente_conta": "Roberto Lima"},
        {"cliente_id": "CLI-005", "nome_cliente": "HealthCare Plus (Fictício)", "segmento": "Saúde", "horas_contratadas_mes": 200, "valor_hora_adicional": 300.00, "gerente_conta": "Carlos Andrade"},
        {"cliente_id": "CLI-006", "nome_cliente": "BioPharma Lab (Fictício)", "segmento": "Saúde", "horas_contratadas_mes": 40, "valor_hora_adicional": 250.00, "gerente_conta": "Roberto Lima"},
        {"cliente_id": "CLI-007", "nome_cliente": "EducaMais EAD (Fictício)", "segmento": "Educação", "horas_contratadas_mes": 50, "valor_hora_adicional": 180.00, "gerente_conta": "Mariana Souza"},
        {"cliente_id": "CLI-008", "nome_cliente": "AgroTech Brasil (Fictício)", "segmento": "Agronegócio", "horas_contratadas_mes": 100, "valor_hora_adicional": 210.00, "gerente_conta": "Carlos Andrade"},
        {"cliente_id": "CLI-009", "nome_cliente": "ConstruForte Eng (Fictício)", "segmento": "Construção", "horas_contratadas_mes": 30, "valor_hora_adicional": 200.00, "gerente_conta": "Roberto Lima"},
        {"cliente_id": "CLI-010", "nome_cliente": "NexGen Energy (Fictício)", "segmento": "Energia", "horas_contratadas_mes": 150, "valor_hora_adicional": 260.00, "gerente_conta": "Mariana Souza"}
    ]
    df_clientes = pd.DataFrame(clientes_data)
    df_clientes_path = os.path.join(data_dir, "clientes.csv")
    df_clientes.to_csv(df_clientes_path, index=False, encoding="utf-8")
    print(f"[OK] {len(df_clientes)} clientes salvos em {df_clientes_path}")

    # ---------------------------------------------------------
    # 2. CHAMADOS (chamados.csv)
    # ---------------------------------------------------------
    consultores = ["Ana Silva", "Carlos Oliveira", "Lucas Mendes", "Mariana Costa", "Rodrigo Santos", "Beatriz Lima"]
    categorias = ["Suporte & Erros", "Desenvolvimento & Melhoria", "Consultoria & Treinamento", "Infraestrutura & Cloud", "Dúvidas Operacionais"]
    prioridades_config = {
        "Crítica": {"sla_resp": 1, "sla_sol": 4, "peso": 0.10},
        "Alta":    {"sla_resp": 2, "sla_sol": 8, "peso": 0.25},
        "Média":   {"sla_resp": 4, "sla_sol": 24, "peso": 0.45},
        "Baixa":   {"sla_resp": 8, "sla_sol": 48, "peso": 0.20}
    }
    
    titulos_exemplos = {
        "Suporte & Erros": [
            "Erro de autenticação no portal do cliente", "Lentidão na geração de relatórios mensais",
            "Falha na integração via API com ERP", "Bug na exibição do gráfico de vendas",
            "Erro de permissão de usuário no módulo financeiro"
        ],
        "Desenvolvimento & Melhoria": [
            "Criação de novo campo personalizado de cadastro", "Implementação de filtro avançado na listagem",
            "Desenvolvimento de exportação em Excel customizada", "Automação do envio de notificações por email",
            "Refatoração da rotina de cálculo de impostos"
        ],
        "Consultoria & Treinamento": [
            "Treinamento da equipe no novo módulo fiscal", "Alinhamento estratégico para migração de sistema",
            "Consultoria de otimização de processos operacionais", "Modelagem de novos relatórios gerenciais",
            "Revisão das regras de negócio do contrato"
        ],
        "Infraestrutura & Cloud": [
            "Aumento de capacidade do servidor de banco de dados", "Configuração de certificado SSL e HTTPS",
            "Backup e restauração de ambiente de testes", "Otimização de queries pesadas no banco",
            "Configuração de rotina de backup em nuvem AWS"
        ],
        "Dúvidas Operacionais": [
            "Esclarecimento sobre regra de encerramento mensal", "Como redefinir permissões de grupo de usuários",
            "Dúvida na importação do arquivo CSV de pedidos", "Orientação sobre parametrização do sistema"
        ]
    }

    start_date = datetime(2026, 2, 1)
    end_date = datetime(2026, 7, 27)
    delta_days = (end_date - start_date).days

    chamados_list = []
    ticket_counter = 1001

    # Generate approx 500 tickets over ~6 months
    for _ in range(520):
        # Pick random client
        client_row = df_clientes.sample(1).iloc[0]
        cli_id = client_row["cliente_id"]
        
        # Pick priority based on weights
        prio = np.random.choice(
            list(prioridades_config.keys()), 
            p=[prioridades_config[k]["peso"] for k in prioridades_config]
        )
        sla_resp_alvo = prioridades_config[prio]["sla_resp"]
        sla_sol_alvo = prioridades_config[prio]["sla_sol"]
        
        cat = random.choice(categorias)
        titulo = random.choice(titulos_exemplos[cat])
        consultor = random.choice(consultores)
        
        # Random opening date
        random_days = random.randint(0, delta_days)
        random_hours = random.randint(8, 18)
        random_minutes = random.randint(0, 59)
        dt_abertura = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        
        # Status distribution: 85% Fechado, 10% Em Andamento, 5% Aguardando Cliente
        status = np.random.choice(["Fechado", "Em Andamento", "Aguardando Cliente"], p=[0.85, 0.10, 0.05])
        
        # Response time calculation (85% within SLA, 15% breached)
        if random.random() < 0.88:
            # Met SLA response
            resp_hours = round(random.uniform(0.1, sla_resp_alvo * 0.9), 2)
            cumpre_resp = True
        else:
            # Breached SLA response
            resp_hours = round(random.uniform(sla_resp_alvo * 1.1, sla_resp_alvo * 2.5), 2)
            cumpre_resp = False
            
        dt_resposta = dt_abertura + timedelta(hours=resp_hours)

        if status == "Fechado":
            # Resolution time (82% within SLA, 18% breached)
            if random.random() < 0.82:
                sol_hours = round(random.uniform(resp_hours + 0.2, sla_sol_alvo * 0.9), 2)
                cumpre_sol = True
            else:
                sol_hours = round(random.uniform(sla_sol_alvo * 1.1, sla_sol_alvo * 2.8), 2)
                cumpre_sol = False
            
            dt_solucao = dt_abertura + timedelta(hours=sol_hours)
            
            # Hours billed/consumed on ticket (dependent on category and resolution time)
            if cat == "Consultoria & Treinamento":
                horas_consumidas = round(random.uniform(2.0, 8.0), 1)
            elif cat == "Desenvolvimento & Melhoria":
                horas_consumidas = round(random.uniform(1.5, 12.0), 1)
            elif prio == "Crítica":
                horas_consumidas = round(random.uniform(2.0, 6.0), 1)
            else:
                horas_consumidas = round(random.uniform(0.5, 3.5), 1)
        else:
            dt_solucao = None
            cumpre_sol = None
            # In progress tickets consumed some partial hours
            horas_consumidas = round(random.uniform(0.5, 4.0), 1)

        chamados_list.append({
            "ticket_id": f"TCK-{ticket_counter}",
            "cliente_id": cli_id,
            "titulo": titulo,
            "categoria": cat,
            "prioridade": prio,
            "data_abertura": dt_abertura.strftime("%Y-%m-%d %H:%M:%S"),
            "data_primeira_resposta": dt_resposta.strftime("%Y-%m-%d %H:%M:%S"),
            "data_solucao": dt_solucao.strftime("%Y-%m-%d %H:%M:%S") if dt_solucao else "",
            "sla_resposta_alvo_hs": sla_resp_alvo,
            "sla_solucao_alvo_hs": sla_sol_alvo,
            "horas_consumidas": horas_consumidas,
            "status": status,
            "consultor": consultor,
            "cumpre_sla_resposta": cumpre_resp,
            "cumpre_sla_solucao": cumpre_sol
        })
        ticket_counter += 1

    df_chamados = pd.DataFrame(chamados_list)
    df_chamados_path = os.path.join(data_dir, "chamados.csv")
    df_chamados.to_csv(df_chamados_path, index=False, encoding="utf-8")
    print(f"[OK] {len(df_chamados)} chamados salvos em {df_chamados_path}")

    # ---------------------------------------------------------
    # 3. HISTÓRICO DE CONSUMO MENSAL (historico_consumo.csv)
    # ---------------------------------------------------------
    # Convert data_abertura to datetime to group
    df_chamados['dt_abertura'] = pd.to_datetime(df_chamados['data_abertura'])
    df_chamados['mes_referencia'] = df_chamados['dt_abertura'].dt.strftime('%Y-%m')
    
    hist_list = []
    meses = sorted(df_chamados['mes_referencia'].unique())
    
    for mes in meses:
        df_mes = df_chamados[df_chamados['mes_referencia'] == mes]
        for _, cli in df_clientes.iterrows():
            cli_id = cli['cliente_id']
            horas_contratadas = cli['horas_contratadas_mes']
            valor_extra = cli['valor_hora_adicional']
            
            chamados_cli_mes = df_mes[df_mes['cliente_id'] == cli_id]
            horas_consumidas = round(chamados_cli_mes['horas_consumidas'].sum(), 1)
            
            # Slight random adjustment if zero to make history realistic
            if horas_consumidas == 0:
                horas_consumidas = round(random.uniform(horas_contratadas * 0.4, horas_contratadas * 1.1), 1)
                
            horas_excedentes = max(0.0, round(horas_consumidas - horas_contratadas, 1))
            faturamento_extra = round(horas_excedentes * valor_extra, 2)
            
            hist_list.append({
                "cliente_id": cli_id,
                "mes_referencia": mes,
                "horas_contratadas": horas_contratadas,
                "horas_consumidas": horas_consumidas,
                "horas_excedentes": horas_excedentes,
                "faturamento_extra": faturamento_extra
            })

    df_hist = pd.DataFrame(hist_list)
    df_hist_path = os.path.join(data_dir, "historico_consumo.csv")
    df_hist.to_csv(df_hist_path, index=False, encoding="utf-8")
    print(f"[OK] {len(df_hist)} registros de historico salvos em {df_hist_path}")
    print("[SUCCESS] Todos os arquivos CSV foram gerados com sucesso na pasta 'data/'!")

if __name__ == "__main__":
    main()
