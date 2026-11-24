# Catálogo completo dos campos

Inventário gerado do catálogo 1.1 do software AEMA 1.0.0 em 24/11/2026.

[Índice do manual](README.md) · [Contratos de dados](projeto/05-DADOS-E-CONTRATOS.md)

São 145 campos catalogados entre métricas, identificação e metadados; isso não significa 145 medições elétricas. A fonte normativa executável é `src/aema/catalog.py`. O traço na coluna de unidade significa que o catálogo não define unidade para aquele campo; não se deve inferir uma.

A coluna Classe descreve o papel do campo. Classe de evidência e tipo de medição se aplicam às métricas. Os métodos são os nomes exatos usados na implementação.

## Fonte `checkin` (81 campos)

| Campo | Unidade | Classe | Evidência / tipo de medição |
|---|---|---|---|
| `anr_count` | count | `numeric_metric` | proxy / `reported_count` |
| `background_partial_count` | count | `numeric_metric` | proxy / `reported_count` |
| `background_partial_current_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `background_partial_max_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `background_partial_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `background_partial_total_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `bluetooth_rx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `bluetooth_tx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `category` | — | `metadata` | metadata |
| `checkin_version` | — | `metadata` | metadata |
| `connectivity_change_count` | count | `numeric_metric` | proxy / `reported_count` |
| `crash_count` | count | `numeric_metric` | proxy / `reported_count` |
| `deep_idle_mode_count` | count | `numeric_metric` | proxy / `reported_count` |
| `deep_idle_mode_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `deep_idling_count` | count | `numeric_metric` | proxy / `reported_count` |
| `deep_idling_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `foreground_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `full_count` | count | `numeric_metric` | proxy / `reported_count` |
| `full_current_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `full_max_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `full_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `full_total_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `full_wakelock_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `interactive_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `is_hidden_or_system_consumer` | — | `metadata` | metadata |
| `light_idle_mode_count` | count | `numeric_metric` | proxy / `reported_count` |
| `light_idle_mode_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `light_idling_count` | count | `numeric_metric` | proxy / `reported_count` |
| `light_idling_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `line_number` | — | `metadata` | metadata |
| `longest_deep_idle_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `longest_light_idle_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `mobile_active_count` | count | `numeric_metric` | proxy / `reported_count` |
| `mobile_active_time_us` | us | `numeric_metric` | proxy / `reported_duration` |
| `mobile_background_rx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `mobile_background_rx_packets` | packets | `numeric_metric` | proxy / `reported_quantity` |
| `mobile_background_tx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `mobile_background_tx_packets` | packets | `numeric_metric` | proxy / `reported_quantity` |
| `mobile_radio_active_adjusted_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `mobile_radio_active_count` | count | `numeric_metric` | proxy / `reported_count` |
| `mobile_radio_active_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `mobile_radio_active_unknown_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `mobile_rx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `mobile_rx_packets` | packets | `numeric_metric` | proxy / `reported_quantity` |
| `mobile_tx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `mobile_tx_packets` | packets | `numeric_metric` | proxy / `reported_quantity` |
| `mobile_wakeup_count` | count | `numeric_metric` | proxy / `reported_count` |
| `partial_count` | count | `numeric_metric` | proxy / `reported_count` |
| `partial_current_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `partial_max_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `partial_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `partial_total_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `partial_wakelock_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `phone_on_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `power_item` | — | `identification` | identification |
| `power_save_enabled_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `process_name` | — | `identification` | identification |
| `proportional_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `screen_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `screen_on_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `start_count` | count | `numeric_metric` | proxy / `reported_count` |
| `system_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `tag` | — | `metadata` | metadata |
| `uid` | — | `identification` | identification |
| `user_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `wakelock_name` | — | `identification` | identification |
| `wifi_background_rx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `wifi_background_rx_packets` | packets | `numeric_metric` | proxy / `reported_quantity` |
| `wifi_background_tx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `wifi_background_tx_packets` | packets | `numeric_metric` | proxy / `reported_quantity` |
| `wifi_rx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `wifi_rx_packets` | packets | `numeric_metric` | proxy / `reported_quantity` |
| `wifi_tx_bytes` | bytes | `numeric_metric` | proxy / `reported_quantity` |
| `wifi_tx_packets` | packets | `numeric_metric` | proxy / `reported_quantity` |
| `wifi_wakeup_count` | count | `numeric_metric` | proxy / `reported_count` |
| `window_count` | count | `numeric_metric` | proxy / `reported_count` |
| `window_current_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `window_max_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `window_time_ms` | ms | `numeric_metric` | proxy / `reported_duration` |
| `window_total_duration_ms` | ms | `numeric_metric` | proxy / `reported_duration` |

Métodos presentes: `batterystats_checkin`.

## Fonte `power` (61 campos)

| Campo | Unidade | Classe | Evidência / tipo de medição |
|---|---|---|---|
| `actual_drain_max_mah` | mAh | `numeric_metric` | estimated / `reported_drain_range` |
| `actual_drain_min_mah` | mAh | `numeric_metric` | estimated / `reported_drain_range` |
| `ambient_display_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `ambient_display_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `audio_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `audio_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `background_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `battery_capacity_mah` | mAh | `numeric_metric` | proxy / `reported_capacity` |
| `bluetooth_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `bluetooth_background_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `bluetooth_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `bluetooth_foreground_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `bluetooth_foreground_service_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `cached_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `camera_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `camera_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `computed_drain_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `cpu_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `cpu_background_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `cpu_cached_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `cpu_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `cpu_foreground_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `cpu_foreground_service_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `foreground_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `foreground_service_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `gnss_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `gnss_cached_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `gnss_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `gnss_foreground_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `gnss_foreground_service_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `idle_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `idle_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `line_number` | — | `metadata` | metadata |
| `measurement_kind` | — | `metadata` | metadata |
| `mobile_radio_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `mobile_radio_background_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `mobile_radio_cached_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `mobile_radio_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `mobile_radio_foreground_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `mobile_radio_foreground_service_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `rated_capacity_mah` | mAh | `numeric_metric` | proxy / `reported_capacity` |
| `record_type` | — | `metadata` | metadata |
| `screen_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `screen_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `sensors_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `sensors_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `total_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `uid_attributed_charge_estimate` |
| `typical_capacity_mah` | mAh | `numeric_metric` | proxy / `reported_capacity` |
| `uid` | — | `identification` | identification |
| `uid_text` | — | `identification` | identification |
| `unit` | — | `metadata` | metadata |
| `video_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `video_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `wakelock_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `wakelock_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `wifi_apps_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `wifi_background_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `wifi_cached_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `wifi_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `wifi_foreground_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |
| `wifi_foreground_service_estimated_charge_mah` | mAh | `numeric_metric` | estimated / `estimated_or_attributed_charge` |

Métodos presentes: `batterystats_power_report`.

## Fonte `packages` (3 campos)

| Campo | Unidade | Classe | Evidência / tipo de medição |
|---|---|---|---|
| `line_number` | — | `metadata` | metadata |
| `package_name` | — | `identification` | identification |
| `uid` | — | `identification` | identification |

Métodos presentes: `pm_package_uid_listing`.

## Consulta pelo software

```powershell
aema inspect --metric computed_drain_mah --source power
aema inspect --source checkin
```

O comando mostra metadados do catálogo. Ele não transforma o campo em uma medida calibrada nem calcula incerteza física.

Para significados de UID compartilhado, origem, payload, valores ausentes e estimativas, consulte os contratos de dados e o glossário.
