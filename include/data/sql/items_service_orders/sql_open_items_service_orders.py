stmt_open_items_service_orders = """
SELECT 
    -- ORDER DE SERVIÇO
    os.cod_empresa,
    os.numero_os,
    os_requisicoes.item,
    os_requisicoes.cod_servico,
    -- PEÇAS E LUBRIFICANTES
    os_requisicoes.cod_item,
    itens.descricao,
    os_requisicoes.quantidade AS qtde_peca,
    CASE
        WHEN os_tipos_empresas.tipo_preco_peca = 'G' 
            THEN NVL((os_requisicoes.preco_garantia * os_requisicoes.quantidade),0)
        ELSE NVL((os_requisicoes.preco_original * os_requisicoes.quantidade),0)
    END AS valor_os
FROM os
    INNER JOIN os_tipos ostp 
        ON os.tipo = ostp.tipo
    INNER JOIN os_requisicoes 
        ON os_requisicoes.cod_empresa = os.cod_empresa
        AND os_requisicoes.numero_os = os.numero_os
    INNER JOIN itens 
        ON os_requisicoes.cod_item = itens.cod_item
    INNER JOIN os_tipos_empresas 
        ON os_tipos_empresas.cod_empresa = os.cod_empresa
        AND os_tipos_empresas.tipo = os.tipo
WHERE TO_CHAR(os.data_emissao, 'YYYY-MM-DD') >= :max_date
  AND os.status_os = '0'
  AND NVL(ostp.garantia, 'N') = 'S'
  AND os.cod_empresa IN ({empresa_ids})
  AND NVL(UPPER(os.orcamento), 'N') = 'N'
  AND os.numero_os > 0
"""
