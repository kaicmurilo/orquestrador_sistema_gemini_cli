# Documento de Arquitetura de Software: PGRS Digital PME

## Visão Geral
O PGRS Digital PME é uma plataforma SaaS focada em automatizar a conformidade ambiental para pequenos geradores de resíduos no Brasil. O sistema simplifica a emissão de Manifestos de Transporte de Resíduos (MTR) e a gestão de Planos de Gerenciamento de Resíduos Sólidos (PGRS), servindo como uma camada de UX e inteligência sobre os portais governamentais (SINIR/SIGOR).

## Componentes

*   **Frontend (React SPA):** Interface *mobile-first* otimizada para operação em campo (pátios e recepções) com baixo consumo de dados.
*   **API Gateway/Backend (Node.js/Express):** Gerencia autenticação, lógica de negócio, regras de validação ambiental e orquestração de documentos.
*   **Banco de Dados (PostgreSQL):** Armazena dados relacionais, histórico de movimentações, metadados de licenças e trilhas de auditoria para fiscalização.
*   **Worker de Integração (Python/FastAPI):** Serviço especializado em comunicação com sistemas governamentais (SINIR/SIGOR), lidando com automação de formulários e extração de dados.
*   **Storage (S3 Compatible):** Repositório seguro para armazenamento de documentos PDF, como Certificados de Destinação Final (CDF) e versões assinadas do PGRS.
*   **Serviço de Notificação:** Gerador de alertas via E-mail/WhatsApp para vencimento de licenças de transportadores e prazos de inventário anual.

## Fluxo de Dados

1.  **Emissão de MTR:** O usuário insere os dados da carga no Frontend -> API valida os dados contra as normas vigentes -> Worker de Integração comunica-se com o SINIR e gera o MTR oficial -> PDF é armazenado no Storage e o link é retornado ao usuário.
2.  **Conciliação de Destinação:** O transportador entrega o resíduo -> O destinador emite o CDF no portal governamental -> O Worker de Integração detecta o novo documento -> API vincula o CDF ao MTR original e atualiza o Dashboard de Conformidade.
3.  **Geração de Inventário:** API consolida todos os registros de movimentação do banco de dados -> Document Engine gera o relatório consolidado para o IBAMA -> Usuário revisa e confirma o envio via plataforma.

## Decisões de Design

*   **Residência de Dados (LGPD):** Hospedagem em região brasileira (ex: AWS `sa-east-1` ou DigitalOcean SP) para garantir baixa latência e total conformidade com a LGPD em relação à soberania de dados nacionais.
*   **Arquitetura Baseada em Workers:** A integração com sistemas do governo é feita de forma assíncrona para que a instabilidade frequente dos portais públicos não bloqueie a experiência do usuário na plataforma.
*   **Priorização de SQL:** O uso de PostgreSQL é fundamental pela natureza transacional e necessidade de integridade referencial rigorosa, garantindo que cada grama de resíduo gerado tenha um destino final auditável.
*   **Agnosticismo de Frontend:** Utilização de React para permitir que a mesma base de código possa ser encapsulada como PWA (Progressive Web App), facilitando a instalação em dispositivos Android/iOS sem as taxas das lojas de aplicativos.
*   **Sustentabilidade Operacional:** Sem dependência de LLMs ou processamento de IA, o custo de infraestrutura é escalável e linear, mantendo a viabilidade da assinatura de baixo ticket (R$ 49 - R$ 250).