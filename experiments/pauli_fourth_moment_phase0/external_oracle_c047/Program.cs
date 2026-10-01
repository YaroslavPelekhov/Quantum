using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;

public sealed class Edge
{
    public int U;
    public int V;
    public Edge(int u, int v) { U = u; V = v; }
}

public sealed class Root
{
    public string Name;
    public int N;
    public List<Edge> Edges;
    public Root(string name, int n, List<Edge> edges) { Name = name; N = n; Edges = edges; }
}

public sealed class MatchingResult
{
    public double Value;
    public List<Edge> Edges;
    public MatchingResult(double value, List<Edge> edges) { Value = value; Edges = edges; }
}

public sealed class SplitMix64
{
    private ulong state;
    private bool hasSpare;
    private double spare;
    public SplitMix64(ulong seed) { state = seed; }
    public ulong NextU64()
    {
        ulong z = (state += 0x9E3779B97F4A7C15UL);
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
        return z ^ (z >> 31);
    }
    public double Uniform() { return ((NextU64() >> 11) + 0.5) / 9007199254740992.0; }
    public double Normal()
    {
        if (hasSpare) { hasSpare = false; return spare; }
        double radius = Math.Sqrt(-2.0 * Math.Log(Uniform()));
        double angle = 2.0 * Math.PI * Uniform();
        spare = radius * Math.Sin(angle);
        hasSpare = true;
        return radius * Math.Cos(angle);
    }
}

public static class Oracle
{
    private static MatchingResult Solve(
        int mask, int n, double[,] weight, bool[,] exists,
        Dictionary<int, MatchingResult> memo)
    {
        if (mask == 0) return new MatchingResult(0.0, new List<Edge>());
        MatchingResult cached;
        if (memo.TryGetValue(mask, out cached)) return cached;
        int v = 0;
        while (((mask >> v) & 1) == 0) v++;
        MatchingResult omitted = Solve(mask & ~(1 << v), n, weight, exists, memo);
        MatchingResult best = new MatchingResult(omitted.Value, new List<Edge>(omitted.Edges));
        for (int u = v + 1; u < n; u++)
        {
            if (((mask >> u) & 1) == 0 || !exists[v, u]) continue;
            MatchingResult tail = Solve(mask & ~(1 << v) & ~(1 << u), n, weight, exists, memo);
            double value = weight[v, u] + tail.Value;
            if (value > best.Value + 1e-14)
            {
                List<Edge> edges = new List<Edge>(tail.Edges);
                edges.Add(new Edge(v, u));
                best = new MatchingResult(value, edges);
            }
        }
        memo[mask] = best;
        return best;
    }

    public static MatchingResult MaximumMatching(Root root, double[] weights)
    {
        double[,] weight = new double[root.N, root.N];
        bool[,] exists = new bool[root.N, root.N];
        for (int i = 0; i < root.Edges.Count; i++)
        {
            Edge e = root.Edges[i];
            weight[e.U, e.V] = weight[e.V, e.U] = weights[i];
            exists[e.U, e.V] = exists[e.V, e.U] = true;
        }
        return Solve((1 << root.N) - 1, root.N, weight, exists,
                     new Dictionary<int, MatchingResult>());
    }

    public static double NuclearNorm(double[,] a)
    {
        int n = a.GetLength(0);
        double[,] s = new double[n, n];
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                for (int k = 0; k < n; k++)
                    s[i, j] -= a[i, k] * a[k, j];
        for (int sweep = 0; sweep < 100 * n * n; sweep++)
        {
            int p = 0, q = 1;
            double maximum = 0.0;
            for (int i = 0; i < n; i++)
                for (int j = i + 1; j < n; j++)
                    if (Math.Abs(s[i, j]) > maximum)
                    { maximum = Math.Abs(s[i, j]); p = i; q = j; }
            if (maximum < 1e-13) break;
            double angle = 0.5 * Math.Atan2(2.0 * s[p, q], s[q, q] - s[p, p]);
            double c = Math.Cos(angle), d = Math.Sin(angle);
            double app = s[p, p], aqq = s[q, q], apq = s[p, q];
            for (int k = 0; k < n; k++)
            {
                if (k == p || k == q) continue;
                double skp = s[k, p], skq = s[k, q];
                s[k, p] = s[p, k] = c * skp - d * skq;
                s[k, q] = s[q, k] = d * skp + c * skq;
            }
            s[p, p] = c * c * app - 2.0 * c * d * apq + d * d * aqq;
            s[q, q] = d * d * app + 2.0 * c * d * apq + c * c * aqq;
            s[p, q] = s[q, p] = 0.0;
        }
        double total = 0.0;
        for (int i = 0; i < n; i++) total += Math.Sqrt(Math.Max(0.0, s[i, i]));
        return total;
    }

    public static double Ratio(Root root, double[] weights, double[] direction, double nu)
    {
        double[,] a = new double[root.N, root.N];
        double quadratic = 0.0;
        for (int i = 0; i < root.Edges.Count; i++)
        {
            Edge e = root.Edges[i];
            a[e.U, e.V] = direction[i];
            a[e.V, e.U] = -direction[i];
            quadratic += direction[i] * direction[i] / weights[i];
        }
        double halfNuclear = NuclearNorm(a) / 2.0;
        return halfNuclear * halfNuclear / (nu * quadratic);
    }
}

public static class Roots
{
    private static void AddEdge(List<Edge> edges, int u, int v) { edges.Add(new Edge(u, v)); }
    public static List<Root> Generate()
    {
        List<Root> roots = new List<Root>();
        for (int n = 3; n <= 9; n++)
        {
            List<Edge> path = new List<Edge>();
            for (int i = 0; i < n - 1; i++) AddEdge(path, i, i + 1);
            roots.Add(new Root("path" + n, n, path));
            List<Edge> cycle = new List<Edge>();
            for (int i = 0; i < n; i++) AddEdge(cycle, i, (i + 1) % n);
            roots.Add(new Root("cycle" + n, n, cycle));
            List<Edge> star = new List<Edge>();
            for (int i = 1; i < n; i++) AddEdge(star, 0, i);
            roots.Add(new Root("star" + n, n, star));
            List<Edge> complete = new List<Edge>();
            for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) AddEdge(complete, i, j);
            roots.Add(new Root("complete" + n, n, complete));
            int left = n / 2;
            List<Edge> bipartite = new List<Edge>();
            for (int i = 0; i < left; i++) for (int j = left; j < n; j++) AddEdge(bipartite, i, j);
            roots.Add(new Root("bipartite" + left + "x" + (n - left), n, bipartite));
            for (int sample = 0; sample < 12; sample++)
            {
                double p = new double[] { 0.25, 0.50, 0.75 }[sample % 3];
                SplitMix64 generator = new SplitMix64((ulong)(470000 + 1000 * n + sample));
                List<Edge> random = new List<Edge>();
                for (int i = 0; i < n; i++)
                    for (int j = i + 1; j < n; j++)
                        if (generator.Uniform() < p) AddEdge(random, i, j);
                if (random.Count == 0) AddEdge(random, 0, 1);
                roots.Add(new Root("er" + n + "_" + sample, n, random));
            }
        }
        return roots;
    }
}

public class Program
{
    private static string HashFile(string path)
    {
        using (SHA256 algorithm = SHA256.Create())
        {
            byte[] hash = algorithm.ComputeHash(File.ReadAllBytes(path));
            StringBuilder text = new StringBuilder();
            foreach (byte value in hash) text.Append(value.ToString("x2"));
            return text.ToString();
        }
    }

    public static int Main()
    {
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
        List<Root> roots = Roots.Generate();
        SplitMix64 generator = new SplitMix64(0xC04720261001UL);
        int weightVectors = 0, randomDirections = 0, violations = 0;
        double maximumRatio = 0.0, minimumRatio = double.PositiveInfinity;
        double maximumTightnessResidual = 0.0;
        string maximumCase = "";
        foreach (Root root in roots)
        {
            for (int trial = 0; trial < 8; trial++)
            {
                double[] weights = new double[root.Edges.Count];
                for (int i = 0; i < weights.Length; i++) weights[i] = 0.2 + 1.8 * generator.Uniform();
                MatchingResult matching = Oracle.MaximumMatching(root, weights);
                weightVectors++;
                for (int directionIndex = 0; directionIndex < 4; directionIndex++)
                {
                    double[] direction = new double[root.Edges.Count];
                    for (int i = 0; i < direction.Length; i++) direction[i] = generator.Normal();
                    double ratio = Oracle.Ratio(root, weights, direction, matching.Value);
                    randomDirections++;
                    if (ratio > maximumRatio) { maximumRatio = ratio; maximumCase = root.Name; }
                    minimumRatio = Math.Min(minimumRatio, ratio);
                    if (ratio > 1.0 + 1e-8) violations++;
                }
                double[] equalityDirection = new double[root.Edges.Count];
                foreach (Edge selected in matching.Edges)
                {
                    for (int i = 0; i < root.Edges.Count; i++)
                    {
                        Edge candidate = root.Edges[i];
                        if ((candidate.U == selected.U && candidate.V == selected.V) ||
                            (candidate.U == selected.V && candidate.V == selected.U))
                        { equalityDirection[i] = weights[i]; break; }
                    }
                }
                double tight = Oracle.Ratio(root, weights, equalityDirection, matching.Value);
                maximumTightnessResidual = Math.Max(maximumTightnessResidual, Math.Abs(tight - 1.0));
            }
        }
        string source = Path.Combine("experiments", "pauli_fourth_moment_phase0", "external_oracle_c047", "Program.cs");
        string protocol = Path.Combine("experiments", "pauli_fourth_moment_phase0", "C047_EXTERNAL_ORACLE_PROTOCOL.md");
        string json = String.Format(CultureInfo.InvariantCulture,
            "{{\n  \"stage\": \"c047_independent_dotnet_skew_oracle\",\n  \"complete\": true,\n" +
            "  \"runtime\": \"{0}\",\n  \"root_graphs\": {1},\n  \"weight_vectors\": {2},\n" +
            "  \"random_directions\": {3},\n  \"equality_directions\": {2},\n" +
            "  \"inequality_violations\": {4},\n  \"maximum_random_ratio\": {5:R},\n" +
            "  \"minimum_random_ratio\": {6:R},\n  \"maximum_ratio_case\": \"{7}\",\n" +
            "  \"maximum_tightness_residual\": {8:R},\n  \"inequality_tolerance\": 1e-8,\n" +
            "  \"tightness_tolerance\": 2e-8,\n  \"source_sha256\": \"{9}\",\n  \"protocol_sha256\": \"{10}\"\n}}\n",
            Environment.Version.ToString(), roots.Count, weightVectors, randomDirections, violations,
            maximumRatio, minimumRatio, maximumCase, maximumTightnessResidual, HashFile(source), HashFile(protocol));
        string output = Path.Combine("results", "pauli_fourth_moment_phase0", "c047_external_oracle.json");
        Directory.CreateDirectory(Path.GetDirectoryName(output));
        File.WriteAllText(output, json, new UTF8Encoding(false));
        Console.WriteLine(json);
        return violations == 0 && maximumTightnessResidual <= 2e-8 ? 0 : 1;
    }
}
