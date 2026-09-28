import { useCallback, useEffect, useState } from 'react';

export function useResource(loader, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setData(await loader());
    } catch (reason) {
      setError(reason.message || 'Could not load this information.');
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
  useEffect(() => { refresh(); }, [refresh]);
  return { data, loading, error, refresh, setData };
}
