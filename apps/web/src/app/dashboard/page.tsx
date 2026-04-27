"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { Asset, Violation } from "@/lib/types";

export default function DashboardPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.assets.list(0, 5),
      api.violations.list(0, 5),
    ])
      .then(([assetsRes, violationsRes]) => {
        setAssets(assetsRes.data);
        setViolations(violationsRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  const protectedCount = assets.filter((a) => a.status === "protected").length;
  const pendingCount = assets.filter((a) => a.status === "pending" || a.status === "fingerprinting").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-600">Overview of your protected assets</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{assets.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Protected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{protectedCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Violations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{violations.length}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Assets</CardTitle>
          </CardHeader>
          <CardContent>
            {assets.length === 0 ? (
              <p className="text-gray-500">No assets yet. Upload your first asset.</p>
            ) : (
              <div className="space-y-3">
                {assets.slice(0, 5).map((asset) => (
                  <div key={asset.id} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{asset.title}</p>
                      <p className="text-sm text-gray-500">{asset.content_type}</p>
                    </div>
                    <Badge
                      variant={
                        asset.status === "protected"
                          ? "success"
                          : asset.status === "failed"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {asset.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Violations</CardTitle>
          </CardHeader>
          <CardContent>
            {violations.length === 0 ? (
              <p className="text-gray-500">No violations detected.</p>
            ) : (
              <div className="space-y-3">
                {violations.slice(0, 5).map((violation) => (
                  <div key={violation.id} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium truncate max-w-[200px]">
                        {violation.discovered_url}
                      </p>
                      <p className="text-sm text-gray-500">{violation.platform}</p>
                    </div>
                    <Badge
                      variant={violation.status === "confirmed" ? "destructive" : "warning"}
                    >
                      {violation.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}