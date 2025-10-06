# Requisitos do Projeto Python

Este documento lista os requisitos iniciais para o desenvolvimento do projeto chamado ReportMe desenvolvido em Python.
Este projeto tem como função principal o desenvolvimento de um portal de relatórios chamado ReportMe. 
- O projeto é composto de dois subprojetos, sendo eles:
    - reportme_api - api desenvolvida em python django 
        - endpoints para o crud das tabelas do sistema, que são basicamente consultas, conexões com banco de dados e estrutura hierárquica.
        - endpoints para a execução das consultas em um banco de dados externo e retornar os dados para a tela ou exportações em arquivos de diferentes formatos.
    - reportme_front - front web com dois ambientes distintos:
        - ambiente administração: conjunto de páginas que fará a administração do crud do portal
        - ambiente de portal de relatórios: onde serão exibidos os projetos existentes para o usuário logado, navegação na hierarquia das consultas e execução das mesmas retornando os dados para a tela ou arquivos para download.

## Requisitos Funcionais

RF-001 - API - Registro novo usuário
RF-002 - API - Esqueci minha senha
    - Solicita o email do usuário
RF-003 - API - Autenticação 
    - Endpoint para autenticação email e senha

RF-004 - API - CRUD Projeto
    - Cadastro projeto
    - Nós do projeto
    - Um nó pode ter N filhos
    - Um nó pode ter zero ou uma query associada
RF-005 - API - CRUD Conexão
    - Cadastro da conexão
    - Teste da conexão
RF-006 - API - CRUD Consulta
    - Cadastro da consulta
    - Cadastro dos parâmetros da consulta
    - Uma consulta pode ter zero ou mais parâmetros
RF-007 - API - CRUD Consulta-Parâmetro
    - Cadastro do parâmetro sempre associado a uma consulta
    - Um parâmetro está sempre associado a uma consulta
RF-008 - API - Rodar consulta
    


RF-201 - FrontEnd - Autenticação
    - Solicita email e senha
    - Apresenta esqueci a senha, solicita o email para recuperação, devolve um link para troca de senha
RF-202 - FrontEnd - Admin CRUD Projeto
    - Apresenta lista de Projetos com Nome
    - Edição de projeto: Nome e árvore. O Primeiro nó do projeto é o Nome do projeto. Criar descendentes.
    - Um nó de projeto pode ter ou não uma query (consulta) associada. 
    - Somente nós folha podem ter consulta.  
RF-203 - FrontEnd - Admin CRUD Conextão
    - Cadastro da conexão
    - Botão para teste da conexão
RF-204 - FrontEnd - Admin CRUD Consulta
    - Espaço para escrever a consulta
    - A consulta pode ter parâmetros identificados pelo prefixo @
RF-205 - FrontEnd - Admin Rodar Consulta em ambiente de teste
    - No cadastro da consulta deve ter um botão para teste da consulta
    - Resultado deve ser apresentado em forma de grid paginado
RF-206 - FrontEnd - Leitor Projetos
    - Deve apresentar os projetos em uma lista e ao escolher um apresentar a árvore. O projeto deve ser apresentado em forma de árvore. Na tela central listar os filhos do nó selecionado. O nó que tem consulta associada deve ter um ícone diferente.
RF-208 - FrontEnd - Leitor Rodar Consulta
    - Ao executar alguma consulta no Leitor de projetos, alternar para a tela de resultado contendo um grid paginado com os resultados.
    - A paginação deve ser de 10, 50, 100.
    - Deve ter um botão para exportação do conteúdo para excel.
    - Deve apresentar a quantidade de resultados na consulta.




## Requisitos Não Funcionais
RNF 001 - Ambiente dividido em: API e FrontEnd
RNF 101 - Ambiente API usando Django REST Framework

RNF-201 - Ambiente FrontEnd Typescript React
RNF-202 - Sistema de login e recuperação de senha
RNF-203 - Ambiente logado com papéis de Admin, Editor e Somente Leitura
RNF-204


## Tecnologias Sugeridas
- API
    - Python versão atual e Django Rest Framework
    - Token-Based Authentication — com JWT
- FRONT
    ReactJS

- Banco de dados do sistema: SQLITE
- Capacidade de execução de consultas em outros bancos de dados, sendo eles:
    - POSTGRES
    - SQL Server
    - Oracle

## Próximos Passos


## Banco de dados - modelo

table_name	column_name	data_type

core_connection	id	INTEGER
core_connection	name	varchar(255)
core_connection	database	varchar(255)
core_connection	host	varchar(255)
core_connection	user	varchar(255)
core_connection	password	varchar(255)

core_parameter	id	INTEGER
core_parameter	name	varchar(255)
core_parameter	type	varchar(50)
core_parameter	allow_null	bool
core_parameter	default_value	Varchar(255)
core_parameter	allow_multiple_values	bool

core_query	id	INTEGER
core_query	name	varchar(255)
core_query	query	TEXT
core_query	connection_id	INTEGER
core_query parameters list of core_parameter

core_query_parameter	id	integer
core_query_parameter	query_id	integer
core_query_parameter	parameter_id	integer

core_project id INTEGER
core_project name varchar(255)
core_project first_node_id INTEGER

core_project_node id INTEGER
core_project_node name varchar(255)
core_project_node parent_id INTEGER
core_project_node query_id
core_project_node connection_id

core_user id INTEGER
core_user email varchar(255)
core_user name varchar(255)
core_user admin BOOLEAN

