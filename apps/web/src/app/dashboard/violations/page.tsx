"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Violation } from "@/lib/types";

export default function ViolationsPage() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const limit = 20;

  useEffect(() => {
    setLoading(true);
    api.violations
      .list(offset, limit)
      .then((res) => {
        setViolations(res.data);
        setTotal(res.meta.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [offset]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Violations</h1>
        <p className="text-gray-600">Detected unauthorized use of your content</p>
      </div>

      {violations.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <p className="text-center text-gray-500">
              No violations detected. Run a scan to check for unauthorized use.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4">
            {violations.map((violation) => (
              <Card key={violation.id}>
                <CardContent className="py-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <p className="font-medium truncate max-w-[300px]">
                        {violation.discovered_url}
                      </p>
                      <p className="text-sm text-gray-500">
                        {violation.platform} •{" "}
                        {violation.confidence.toFixed(1%)} confidence
                      </p>
                      <p className="text-xs text-gray-400">
                        {new Date(violation.detected_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <Badge
                        variant={
                          violation.status === "confirmed"
                            ? "destructive"
                            : violation.status === "dmca_sent"
                            ? "success"
                            : "warning"
                        }
                      >
                        {violation.status}
                      </Badge>
                      {violation.estimated_reach && (
                        <span className="text-xs text-gray-500">
                          ~{violation.estimated_reach.toLocaleString()} reach
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Showing {violations.length} of {total} violations
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - limit))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={offset + limit >= total}
                onClick={() => setOffset(offset + limit)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}