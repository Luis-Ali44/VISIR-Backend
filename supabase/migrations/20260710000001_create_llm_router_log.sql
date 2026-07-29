CREATE TABLE llm_router_log (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    id_organizacion    uuid REFERENCES organizaciones(id) ON DELETE SET NULL,
    tier_solicitado    varchar(20) NOT NULL,
    tier_usado         varchar(20) NOT NULL,
    motivo_fallback    varchar(100),
    complejidad_score  float,
    tokens_entrada     int,
    tokens_salida      int,
    latencia_ms        int,
    exito              boolean NOT NULL DEFAULT true,
    created_at         timestamp NOT NULL DEFAULT now()
);

CREATE INDEX idx_llm_router_log_org_fecha ON llm_router_log (id_organizacion, created_at DESC);
CREATE INDEX idx_llm_router_log_tier ON llm_router_log (tier_usado, created_at DESC);
