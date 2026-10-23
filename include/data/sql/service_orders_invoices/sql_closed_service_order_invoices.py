stmt_closed_service_order_invoices = """
            SELECT 
                  os.cod_empresa,
                  os.numero_os,
                  '' as nr_sg,
                  (CASE WHEN vendas.nfe='S' THEN '2'
                  ELSE '1' END) AS tipo_nota_fiscal,
                  vendas.controle AS nr_nota_fiscal,
                  vendas.emissao AS data_referencia,
                  vendas.total_nota AS valor
            FROM  os 
                  INNER JOIN os_tipos ostp ON (os.tipo = ostp.tipo)
                  INNER JOIN vendas ON (vendas.cod_empresa = os.cod_empresa AND vendas.numero_os = os.numero_os)
                  INNER JOIN operacoes ON (operacoes.cod_empresa = vendas.cod_empresa AND operacoes.cod_operacao = vendas.cod_operacao)
            WHERE to_char(os.data_encerrada,'YYYY-MM-dd') >=  :max_date 
              AND nvl(upper(ostp.garantia),'N')='S'
              AND vendas.status!='1'
              AND os.cod_empresa IN ({empresa_ids})
              AND operacoes.Cod_Operacao='3'
            ORDER BY os.cod_empresa,os.numero_os
            """
