create or replace view hospital_santa_rosa.gold_fluxo.vw_dim_source as
select * from values
    ('silver_atendimento_emergencia', 'Emergência'),
    ('silver_cirurgias', 'Cirúrgico'),
    ('silver_internacoes', 'Internação'),
    ('silver_exames_imagem', 'Exames de Imagem'),
    ('silver_exames_laboratoriais', 'Exame Laboratorial'),
    ('silver_altas', 'Alta'),
    ('silver_movimentacoes', 'Movimentações')
as t(source, source_label);