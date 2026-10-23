stmt_closed_service_order_complaint = """
                        SELECT
                            -- ORDEM DE SERVIÇO
                            os.cod_empresa,
                            os.numero_os,

                            -- RECLAMAÇÃO FEITA PELO CLIENTE
                            TRIM(UPPER(os_original.descricao)) AS reclamacao,
                            os_original.item

                        FROM os
                            INNER JOIN os_tipos ostp
                                ON os.tipo = ostp.tipo

                            LEFT JOIN os_original
                                ON os_original.numero_os = os.numero_os
                            AND os_original.cod_empresa = os.cod_empresa
                        WHERE to_char(os.data_encerrada,'YYYY-MM-DD') >= :max_date
                            AND NVL(ostp.garantia, 'N') = 'S'
                            AND os.cod_empresa IN ({empresa_ids})
                            AND NVL(UPPER(os.orcamento), 'N') = 'N'
                            AND os.numero_os > 0
                        ORDER BY
                            os.cod_empresa,
                            os.numero_os,
                            os_original.item ASC"""
