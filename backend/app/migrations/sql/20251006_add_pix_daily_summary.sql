-- View materializada de métricas diárias (segura para produção)
-- Recalcula volume/contagem/média e contas ativas por dia.

-- 1) Dropar a MV anterior (se existir) de forma segura
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_matviews WHERE matviewname = 'pix_daily_summary'
  ) THEN
    EXECUTE 'DROP MATERIALIZED VIEW CONCURRENTLY IF EXISTS pix_daily_summary';
  END IF;
END$$;

-- 2) Criar MV
CREATE MATERIALIZED VIEW pix_daily_summary AS
SELECT
  date_trunc('day', pt.created_at AT TIME ZONE 'UTC')::date AS day_utc,
  COUNT(*)::bigint                                  AS total_count,
  SUM(pt.amount)::numeric(18,2)                     AS total_amount,
  AVG(pt.amount)::numeric(18,2)                     AS avg_amount,
  MIN(pt.amount)::numeric(18,2)                     AS min_amount,
  MAX(pt.amount)::numeric(18,2)                     AS max_amount,
  COUNT(DISTINCT pt.from_account_id)                AS distinct_senders,
  COUNT(DISTINCT pt.to_account_id)                  AS distinct_receivers,
  COUNT(DISTINCT a.account_id)                      AS accounts_active
FROM pix_transactions pt
LEFT JOIN LATERAL (
  SELECT unnest(ARRAY[pt.from_account_id, pt.to_account_id]) AS account_id
) a ON TRUE
GROUP BY 1
ORDER BY 1;

-- 3) Índices para acelerar filtros por intervalo e ordenação
CREATE UNIQUE INDEX IF NOT EXISTS idx_pix_daily_summary_day_utc
  ON pix_daily_summary (day_utc);

-- (Opcional) covering index para ordenação desc
CREATE INDEX IF NOT EXISTS idx_pix_daily_summary_day_utc_desc
  ON pix_daily_summary (day_utc DESC);

-- 4) Comentário (documentação)
COMMENT ON MATERIALIZED VIEW pix_daily_summary IS
'Resumo diário de PIX: contagem, volume, média, min, max e contas ativas. Base UTC.';

