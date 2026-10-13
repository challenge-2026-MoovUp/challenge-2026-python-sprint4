-- Rode UMA vez, só se as tabelas ainda não existem no seu schema.
CREATE TABLE usuario (
    id_usuario NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome       VARCHAR2(100) NOT NULL,
    email      VARCHAR2(150) NOT NULL UNIQUE,
    pontos     NUMBER DEFAULT 0 NOT NULL CHECK (pontos >= 0)
);

CREATE TABLE historico (
    id_historico NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario   NUMBER NOT NULL,
    descricao    VARCHAR2(200) NOT NULL,
    CONSTRAINT fk_historico_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario) ON DELETE CASCADE
);

INSERT INTO usuario (nome, email, pontos) VALUES ('Maria Teste', 'maria@teste.com', 0);
COMMIT;

SELECT * FROM usuario;
