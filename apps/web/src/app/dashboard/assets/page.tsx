"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Asset } from "@/lib/types";

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const limit = 20;

  useEffect(() => {
    setLoading(true);
    api.assets
      .list(offset, limit)
      .then((res) => {
        setAssets(res.data);
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Assets</h1>
          <p className="text-gray-600">Manage your protected content</p>
        </div>
        <Link href="/dashboard/upload">
          <Button>Upload Asset</Button>
        </Link>
      </div>

      {assets.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <p className="text-center text-gray-500">
              No assets yet. Upload your first asset to get started.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4">
            {assets.map((asset) => (
              <Card key={asset.id}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{asset.title}</p>
                      <p className="text-sm text-gray-500">
                        {asset.content_type} • {new Date(asset.created_at).toLocaleDateString()}
                      </p>
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
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Showing {assets.length} of {total} assets
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