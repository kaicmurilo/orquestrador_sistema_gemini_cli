Com base na pesquisa de mercado realizada, elaborei o documento de arquitetura de software para o **EcoScale SMB**.

```markdown
# Arquitetura de Software: EcoScale SMB (ESG Compliance for Suppliers)

## Visão Geral
O EcoScale SMB é uma plataforma SaaS projetada para automatizar a conformidade ESG de pequenas e médias empresas que atuam como fornecedoras de grandes corporações. A arquitetura foca na ingestão automatizada de dados financeiros e contábeis, utilizando IA para classificar emissões e gerar relatórios prontos para auditoria, garantindo que as PMEs mantenham seus contratos sob novas regulações globais.

## Componentes

*   **EcoScale Web Portal (Frontend):** Dashboard em React/Next.js que oferece interfaces distintas para fornecedores (input de dados e visualização de score) e compradores enterprise (gestão da cadeia de suprimentos).
*   **API Gateway / Backend Service:** Núcleo em Node.js (NestJS) que gerencia autenticação, orquestração de fluxos e regras de negócio ESG.
*   **Data Integration Layer (Connectors):** Módulo que utiliza Codat.io ou Plaid para conectar-se a ERPs (QuickBooks, SAP, Xero) e extrair faturas de utilidades e logística.
*   **AI Classification Engine:** Serviço que utiliza LLMs (GPT-4o/Claude) para categorizar descrições de gastos brutos em categorias específicas de emissões de Escopo 1, 2 e 3.
*   **Emission Calculation Engine:** Motor de cálculo que aplica fatores de emissão oficiais (ex: DEFRA, EPA) aos dados categorizados para mensurar a pegada de carbono.
*   **Audit-Ready Report Generator:** Serviço dedicado à geração de documentos PDF/JSON em conformidade com os padrões regulatórios (CSRD, VSME).
*   **Persistence Layer (PostgreSQL):** Banco de dados relacional para armazenamento de dados transacionais, trilhas de auditoria imutáveis e evidências de governança.

## Fluxo de Dados

1.  **Ingestão:** O fornecedor PME autoriza a conexão do seu ERP através da *Data Integration Layer*.
2.  **Processamento:** Os dados de faturas e gastos são enviados para o *AI Classification Engine*, que identifica o tipo de atividade (ex: "Compra de Diesel" ou "Conta de Luz").
3.  **Cálculo:** O *Emission Calculation Engine* recebe as atividades categorizadas e aplica os fatores de conversão para CO2e e outros KPIs de sustentabilidade.
4.  **Enriquecimento:** O usuário completa questionários guiados no portal para dados qualitativos (Social e Governança).
5.  **Armazenamento:** Todos os dados processados e cálculos intermediários são salvos no *PostgreSQL* para garantir rastreabilidade.
6.  **Entrega:** O *Report Generator* consolida as informações em um relatório certificado, que é disponibilizado ao comprador Enterprise via *Buyer Portal*.

## Decisões de Design

*   **Arquitetura Baseada em IA para Classificação:** O uso de LLMs elimina a necessidade de mapeamento manual de contas contábeis, reduzindo drasticamente a fricção de entrada para o usuário PME.
*   **Banco de Dados Relacional (PostgreSQL):** Escolhido pela necessidade crítica de integridade referencial e suporte a transações complexas, fundamentais para gerar trilhas de auditoria que suportem verificações externas.
*   **Modular Monolith:** Para o MVP, adotamos um monolito modular para acelerar o desenvolvimento, mantendo a separação clara entre os motores de cálculo e os conectores, permitindo a transição para microserviços conforme a escala de integração cresça.
*   **Abstração de Integrações (Codat/Plaid):** O uso de agregadores de terceiros permite suportar centenas de ERPs diferentes desde o dia 1, focando os recursos internos no core business de inteligência ESG.
```