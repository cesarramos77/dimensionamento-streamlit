import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import locale
import datetime as dt

# Definindo a localização para o Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Aqui ficaria a definição das funções que você já tem, como `calculate_agents_needed`, `calculate_max_capacity` e `simulate_scenarios`
def calculate_agents_needed(arrival_rate, service_time, max_wait_time, abandonment_rate, unavailability_percentage, patience_time):
    # Considerando os novos parâmetros

    total_calls_received = arrival_rate / (1 - abandonment_rate)
    exceeded_threshold = total_calls_received * (1 - 0.8)  # 20% das chamadas excedem os 20 segundos de espera

    service_time_hours = service_time / 3600
    max_wait_hours = max_wait_time / 3600

    agents_needed = (exceeded_threshold * service_time_hours) / max_wait_hours

    return round(agents_needed)


def calculate_max_capacity(agents, service_time, productive_time):
    # Considerando os novos parâmetros 

    max_capacity = (productive_time / service_time) * agents

    return round(max_capacity)


def calculate_agents_per_hour(arrival_rate, service_time, max_wait_time, abandonment_rate, unavailability_percentage, patience_time):
    # Função para calcular a quantidade de consultores necessários por hora

    agents_per_hour = {}
    productive_time_per_hour = 6.83 * 3600  # 6 horas e 50 minutos em segundos

    for hour in range(8, 20):
        arrival_rate_per_hour = arrival_rate / 12  # Distribuído igualmente ao longo das 12 horas
        agents_needed = calculate_agents_needed(arrival_rate_per_hour, service_time, max_wait_time, abandonment_rate, unavailability_percentage, patience_time)
        agents_capacity = calculate_max_capacity(agents_needed, service_time, productive_time_per_hour)

        agents_per_hour[f"{hour}:00-{hour + 1}:00"] = agents_needed
        productive_time_per_hour += 3600  # Incrementando uma hora

    return agents_per_hour

def simulate_scenarios(arrival_rate, interval_rate, service_time, max_wait_time, abandonment_rate, unavailability_percentage, patience_time, productive_time):
    # Calculando a quantidade de consultores líquida do dia
    consultor = calculate_agents_needed(arrival_rate, service_time, max_wait_time, abandonment_rate, unavailability_percentage, patience_time) / interval_rate
    hc_productive = consultor * (1 - unavailability_percentage)
    total_volume = arrival_rate * interval_rate
    max_capacity = calculate_max_capacity(consultor, service_time, productive_time) / consultor

    # Calculando o incremento e os cenários
    increase_l = hc_productive / interval_rate
    increase_g = consultor / interval_rate
    
    scenarios = {}
    for i in range(1, 13):
        key = round(i * increase_g)
        ns = i * increase_l
        value = ((ns * max_capacity) / total_volume) * 0.8  # Calculando a porcentagem de ligações atendidas em até 20 segundos
        scenarios[key] = value

    return scenarios


# #Grafico
# Função para gerar o gráfico de barras
def plot_chart(scenarios):
    keys = list(scenarios.keys())
    values = list(scenarios.values())

    df = pd.DataFrame({'Quantidade de Agentes': keys, '% de Ligações Atendidas': values})

    fig, ax = plt.subplots(figsize=(16, 8))

    above_threshold = df[df['% de Ligações Atendidas'] > 0.75]
    below_threshold = df[df['% de Ligações Atendidas'] <= 0.75]

    ax.bar(above_threshold['Quantidade de Agentes'], above_threshold['% de Ligações Atendidas'], color='lightblue', width=5.0, linewidth=1.5, label='Acima de 0.75')
    ax.bar(below_threshold['Quantidade de Agentes'], below_threshold['% de Ligações Atendidas'], color='red', width=5.0, linewidth=1.5, label='Abaixo de 0.75')

    ax.set_xlabel('Quantidade de Agentes', fontsize=15, fontweight='bold')
    ax.set_ylabel('% de Ligações Atendidas em até 20 segundos', fontsize=15, fontweight='bold')
    ax.set_title('Qualidade do Atendimento (Nível de Serviço) em função da Quantidade de Agentes', fontsize=15, fontweight='bold')
    ax.set_xticks(keys)
    ax.tick_params(axis='both', labelsize=15)
    for key, value in scenarios.items():
        ax.text(key, value, f'{value*100:.2f}%', ha='center', va='bottom', fontsize=15, fontweight='bold')
    ax.axhspan(0.75, 1, color='lightgreen', alpha=0.3)
    ax.grid(False)
    ax.set_yticklabels([])  # Remove os rótulos do eixo y
    plt.tight_layout()

    return fig  # Retorna a figura gerada

#Função para converter segundos em horas
# Função para converter segundos em formato de horas (hh:mm:ss)
def convert_seconds_to_hh(seconds):
    tma_timedelta = dt.timedelta(seconds=seconds)
    return str(tma_timedelta)

def calculate_dia_mes(volume):
    volume_dia = volume * 12 #12 representa os 12 intervalos em horas que a operação atende
    volume_mes = volume_dia * 22
    #Formatar para visual em portugues
    arrival_rate_day = locale.format_string("%.0f",volume_dia, grouping=True)
    arrival_rate_month = locale.format_string("%.0f",volume_mes, grouping=True)
    return arrival_rate_day, arrival_rate_month

# Criando a interface com Streamlit
def main():
    st.title('Dimensionamento do Call Center')
    # Intruções de Uso
    #indicadores:
    # IAB representa a taxa de abandono
    iab = """
    Taxa de Abandono > 
     IAB conhecido por índice de abandono ajuda a mensurar o quão efetivo está o atendimento receptivo 
    em um contact center. Para calculá-lo, pegamos o número de ligações abandonadas 
    acima do nível de serviço e o dividimos pela soma dessas chamadas e das atendidas, 
    tanto dentro quanto fora do limiar ideal definido para a operação.
    """
    
    tma = """
    Tempo Médio de Atendimento > 
     O TMA é um índice de grande influência no custo, e deve ser acompanhado e constantemente trabalhado
    para sua redução ou manutenção. A diferença de poucos segundos em uma ligação tem grande impacto no 
    custo operacional do call center e afeta diretamente a capacidadede atendimento. 
    """
    
    st.write(iab)
    st.write('')
    st.write(tma)
    # Adicionar os outros parâmetros como sliders ou inputs conforme necessário
    interval_rate = 12 # Quantidade de intervalos para o dia de trabalho
    max_wait_time = 20  # Tempo máximo de espera em segundos por cliente aguardando em linha para ser atendido
    productive_time = 6.83*3600 # Equivale dizer que é carga produtiva de 6 horas e 50 minutos em segundos
    patience_time = 100  # Tempo máximo de paciência do cliente aguardando em fila antes de abandonar a ligação

    st.sidebar.title('Parâmetros')
    arrival_rate = st.sidebar.slider('**Volume de Chamadas/Hora**', 50, 1000, 468)
    arrival_rate_day = calculate_dia_mes(arrival_rate)[0]
    arrival_rate_month = calculate_dia_mes(arrival_rate)[1]
    st.sidebar.text(f'Chamadas Recebidas (dia) : {arrival_rate_day}')
    st.sidebar.text(f'Chamadas Recebidas (mês) : {arrival_rate_month}')
    st.sidebar.markdown("________________________________")
    service_time = st.sidebar.slider('**Tempo Médio Atendimento (Segundos) - TMA**', 50, 600, 300)  # Tempo médio de atendimento em segundos por ligação atendida
    service_time_hh = convert_seconds_to_hh(service_time)
    st.sidebar.text(f'TMA em minutos : {service_time_hh}')
    st.sidebar.markdown("________________________________")
    abandonment_rate = (st.sidebar.slider('**Taxa Abandono % (IAB)**',3, 15, 5) /100)  # Taxa de abandono de clientes no dia entre 08:00 e 19:00.
    unavailability_percentage = (st.sidebar.slider('**Taxa Indisponiblidade % (TI)**', 35, 50, 38) / 100) # % Total de indisponibilidade do dia de atendimento considerando entre 08:00 e 19:00.   
    hc_vailability = 1 - unavailability_percentage # % de disponiblidade da operação
    convert_hc_liq_hc_pa = 1 + hc_vailability 
       
    if st.sidebar.button('Gerar Cenários'):
        scenarios = simulate_scenarios(arrival_rate, interval_rate, service_time, max_wait_time, abandonment_rate, unavailability_percentage, patience_time, productive_time)  
        #Exibindo uma Narrativa ao usuário
        # Calcular a quantidade de consultores necessária para atender 80% do volume de ligações em até 20 segundos de espera
        consultor = (calculate_agents_needed(arrival_rate, service_time, max_wait_time, abandonment_rate, unavailability_percentage, patience_time) / interval_rate)
        total_volume_day = arrival_rate * interval_rate
        max_capacity = calculate_max_capacity(consultor, service_time, productive_time) / consultor
        total_volume_month = total_volume_day * 22
        
        # Exibe os cenários como uma tabela
        df_scenarios = pd.DataFrame(scenarios.items(), columns=['Quantidade de Agentes', '% de Ligações Atendidas'])
        df_scenarios['% de Ligações Atendidas'] = (df_scenarios['% de Ligações Atendidas'] * 100).apply(lambda x: "{:.2f}%".format(x))
        df_scenarios['Cap. Max. Atend.'] = round((df_scenarios['Quantidade de Agentes'] * hc_vailability) * max_capacity)
        df_scenarios['Cap. Max. Atend.'] = df_scenarios['Cap. Max. Atend.'].apply(lambda x: locale.format_string("%.0f",x, grouping=True))
        st.table(df_scenarios)
        
        
         #Formatar total_volume e max_capacity com separadores de milhares
        f_total_volume_day = locale.format_string("%.0f",total_volume_day, grouping=True)
        f_total_volume_month = locale.format_string("%.0f",total_volume_month, grouping=True)
        tma_t_delta = dt.timedelta(seconds=service_time)
        tma_hh = str(tma_t_delta)
        
        st.write(f"Com base nos parâmetros fornecidos, a empresa precisará de aproximadamente {int(consultor)} consultores AC para atender um volume de aproximadamente {f_total_volume_day} de chamadas ao dia e no mês entregará {f_total_volume_month} cases, considerando o horário de trabalho das 08:00 às 18:30. A capacidade média de atendimento de 1 do consultor é de {int(max_capacity)} chamadas por dia com TMA de {tma_hh}.")

        figura = plot_chart(scenarios)
        st.pyplot(figura)

if __name__ == '__main__':
    main()
