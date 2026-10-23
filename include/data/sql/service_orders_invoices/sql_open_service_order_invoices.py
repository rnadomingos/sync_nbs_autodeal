stmt_open_service_order_invoices = """  
        SELECT 
            os.cod_empresa,
            os.numero_os,
            '' AS nr_sg,
            CASE 
                WHEN vendas.nfe = 'S' THEN '1'
                ELSE '2' 
            END AS tipo_nota_fiscal,
            nvl(vendas.controle,0) AS nr_nota_fiscal,
            vendas.emissao AS data_referencia,
            vendas.total_nota AS valor
        FROM os
        INNER JOIN os_tipos ostp ON (os.tipo = ostp.tipo)
        LEFT JOIN vendas ON (vendas.cod_empresa = os.cod_empresa AND vendas.numero_os = os.numero_os)
        LEFT JOIN operacoes ON (operacoes.cod_empresa = vendas.cod_empresa AND operacoes.cod_operacao = vendas.cod_operacao)
        WHERE to_char(os.data_emissao,'YYYY-MM-dd') >=  :max_date 
          AND os.status_os = '0'
          AND NVL(ostp.garantia, 'N') = 'S'
          AND os.cod_empresa IN ({empresa_ids})
          AND NVL(UPPER(os.orcamento), 'N') = 'N'
          AND NVL(vendas.controle,0) > 0
          ORDER BY 
            os.cod_empresa,
            os.numero_os
"""
