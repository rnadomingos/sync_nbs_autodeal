stmt_closed_related_service_orders = """SELECT 
    os.cod_empresa,
    os.numero_os,
    os_relacoes.numero_os_irma
FROM os
  LEFT JOIN os_relacoes ON (os.cod_empresa = os_relacoes.cod_empresa AND os.numero_os = os_relacoes.numero_os)
  INNER JOIN os_tipos ostp ON (os.tipo = ostp.tipo)
WHERE to_char(os.data_encerrada,'YYYY-MM-dd') >= :max_date  -- primeira carga
-- AND to_char(os.data_emissao,'YYYY-MM-dd') >= :max_date 
AND NVL(ostp.garantia, 'N') = 'S'
AND os.cod_empresa IN ({empresa_ids})
  --AND OS.NUMERO_OS>'0'
AND NVL(UPPER(os.orcamento), 'N') = 'N'
ORDER BY 
    os.cod_empresa,
    os.numero_os
"""
