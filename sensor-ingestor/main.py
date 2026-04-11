#!/usr/bin/env python3
"""Entry point for the sensor-ingestor MVP skeleton."""

from __future__ import annotations

import argparse
import json
import time

from sensor_ingestor.runtime import SensorIngestorService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="data/examples/sensor_ingestor_config_seed.json")
    parser.add_argument("--catalog", default=None)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop-interval-seconds", type=int, default=30)
    parser.add_argument("--limit-sensor-groups", type=int, default=None)
    parser.add_argument("--limit-device-groups", type=int, default=None)
    parser.add_argument("--serve-port", type=int, default=None)
    args = parser.parse_args()

    service = SensorIngestorService.from_files(config_path=args.config, catalog_path=args.catalog)

    if args.serve_port is not None:
        service.start_http_server(args.serve_port)

    summary = service.run_once(
        limit_sensor_groups=args.limit_sensor_groups,
        limit_device_groups=args.limit_device_groups,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.once:
        return

    try:
        while True:
            time.sleep(args.loop_interval_seconds)
            summary = service.run_once(
                limit_sensor_groups=args.limit_sensor_groups,
                limit_device_groups=args.limit_device_groups,
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2))
    except KeyboardInterrupt:
        service.stop_http_server()


if __name__ == "__main__":
    main()
