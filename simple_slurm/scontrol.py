import os
import subprocess
import csv
from io import StringIO


class SlurmScontrolWrapper:
    def __init__(self):
        self.command = "scontrol"
        self.default_format = '"%i","%j","%t","%M","%L","%D","%C","%m","%b","%R"'
        self.output_format = os.getenv("SCONTROL_FORMAT", self.default_format)

        if not self._is_valid_csv_format(self.output_format):
            raise ValueError(
                "Invalid CSV format in SCONTROL_FORMAT environment variable"
            )

        self.jobs = {}

    def show_job(self, job_id: int) -> dict[str, str]:
        """Refresh the information from the current queue for the current user"""
        result = subprocess.run(
            [self.command, "-o", self.output_format, f"{job_id}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Error running scontrol: {result.stderr}")

        serialized_result = self._parse_output(result.stdout)
        self.jobs[serialized_result["JobId"]] = serialized_result
        return serialized_result

    def _is_valid_csv_format(self, format_str: str):
        """validates that the output is a valid csv"""
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(format_str, delimiters=",")
            dialect.strict = True
            csv.reader(StringIO(format_str), dialect=dialect)
            return True
        except csv.Error:
            return False

    def _parse_output(self, stdout: str):
        """converts the stdout into a python dictionary
        appends split values missing '=' to the previous element
        """

        pairs: list[str] = []
        for e in stdout.split():
            if "=" in e:
                pairs.append(e)
            else:
                pairs[-1] += f"_{e}"

        return {k: v for k, v in (pair.split("=", 1) for pair in pairs)}
