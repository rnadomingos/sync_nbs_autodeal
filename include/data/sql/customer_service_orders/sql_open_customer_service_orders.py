stmt_open_customer_service_orders = """SELECT 
      --ORDEM DE SERVICO
      os.cod_empresa,
      os.numero_os,
      --DADOS CLIENTE
      TRIM(UPPER(cli.nome)) AS NOME_CLIENTE,
      (CASE 
	      WHEN cli.cod_classe = 'F' THEN LPAD(cli.cod_cliente, 11, 0)
	      WHEN cli.cod_classe = 'J' THEN LPAD(cli.cod_cliente, 14, 0)
      END) AS CPF_CNPJ,      
      '' as telefone,
      '' as celular   	
FROM    os 
        inner join empresas emp on (os.cod_empresa = emp.cod_empresa)
        inner join clientes cli on (os.cod_cliente = cli.cod_cliente)
        inner join os_tipos ostp on (os.tipo = ostp.tipo)
        left join empresas_usuarios usu2 on (os.quem_abriu = usu2.nome)
        left join os_dados_veiculos dados on (os.cod_empresa = dados.cod_empresa and os.numero_os = dados.numero_os)
where to_char(os.data_emissao,'YYYY-MM-dd') >= :max_date --'2025-07-01'
and os.status_os='0'
AND nvl(ostp.garantia,'N')='S'
AND os.cod_empresa IN ({empresa_ids})
and nvl(upper(os.orcamento),'N')='N'
AND OS.NUMERO_OS > 0"""
