stmt_closed_service_order_services = """
                -- SCRIPT PARA ATUALIZAR OS SERVIÇOS DAS OSs NO FECHAMENTO NA TABELA OS_SERVICOS
                SELECT
                    -- ORDEM DE SERVIÇO
                    os.cod_empresa,
                    os.numero_os,   
                    -- SERVIÇOS
                    os_servicos.item,
                    SUBSTR(os_servicos.cod_servico, 0, 11) AS codigo_servico,
                    os_servicos.defeito AS cod_defeito,
                    TRIM(UPPER(SUBSTR(serv.descricao_servico, 1, 160))) AS descritivo,
                    os_servicos.preco_venda AS valor
                FROM os
                    INNER JOIN os_tipos ostp ON (os.tipo = ostp.tipo)
                    INNER JOIN os_servicos ON (os_servicos.cod_empresa = os.cod_empresa AND os_servicos.numero_os  = os.numero_os)
                    INNER JOIN servicos serv ON (serv.cod_servico = os_servicos.cod_servico)
                WHERE TO_CHAR(os.data_encerrada, 'YYYY-MM-DD') >= :max_date
                    AND NVL(ostp.garantia, 'N') = 'S'
                    AND os.cod_empresa IN ({empresa_ids})
                    AND NVL(UPPER(os.orcamento), 'N') = 'N'
                ORDER BY
                    os.cod_empresa,
                    os.numero_os,
                    os_servicos.item"""
