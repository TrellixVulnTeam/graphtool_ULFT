#! /usr/bin/env python
# graph_tool.py -- a general graph manipulation python module
#
# Copyright (C) 2007 Tiago de Paula Peixoto <tiago@forked.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Centrality
==========

This module includes centrality-related algorithms.
"""

from .. dl_import import dl_import
dl_import("import libgraph_tool_centrality")

from .. core import _prop
import numpy

__all__ = ["pagerank", "betweenness", "central_point_dominance", "eigentrust",
           "absolute_trust"]

def pagerank(g, damping=0.8, prop=None, epslon=1e-6, max_iter=None,
             ret_iter=False):
    r"""
    Calculate the PageRank of each vertex.

    Parameters
    ----------
    g : Graph
        Graph to be used.
    damping : float, optional (default: 0.8)
        Damping factor.
    prop : ProperyMap, optional (default: None)
        Vertex property map to store the PageRank values.
    epslon : float, optional (default: 1e-6)
        Convergence condition. The iteration will stop if the total delta of all
        vertices are below this value.
    max_iter : int, optional (default: None)
        If supplied, this will limit the total number of iterations.
    ret_iter : bool, optional (default: False)
        If true, the total number of iterations is also returned.

    Returns
    -------
    A vertex property map containing the PageRank values.

    See Also
    --------
    betweenness: betweenness centrality
    eigentrust: eigentrust centrality
    absolute_trust: absolute trust centrality

    Notes
    -----
    The value of PageRank of vertex v :math:`PR(v)` is given interactively by
    the relation:

    .. math:
        PR(v) = \frac{1-d}{N} + d \sum_{w \in \Gamma^{-}(v)}
                \frac{PR (w)}{d^{+}(w)}</math>

    where :math:`\Gamma^{-}(v)` are the in-neighbours of v, :math:`d^{+}(w)` is
    the out-degree of w, and d is a damping factor.

    The implemented algorithm progressively iterates the above condition, until
    it no longer changes, according to the parameter epslon. It has a
    topology-dependent running time.

    If enabled during compilation, this algorithm runs in parallel.

    Examples
    --------
    >>> from numpy.random import poisson
    >>> g = gt.random_graph(100, lambda: (poisson(3), poisson(3)), seed=42)
    >>> pr = gt.pagerank(g)
    >>> print pr.get_array()
    [ 1.23631405  1.26200483  1.96751522  0.64733031  0.70919769  0.30955985
    1.52538634  0.61243582  0.53488703  0.5495016   0.63962998  0.45806361
    1.67723278  0.26623242  0.32215029  0.53362967  0.32231378  0.33050213
    0.5356975   0.37390974  0.93677559  0.38228945  0.36843877  0.84068062
    1.06194997  0.53691497  1.13629299  1.16796209  0.55409311  0.75573135
    0.58224114  0.40017455  0.35638757  1.16638209  0.74002981  0.47176731
    0.42552094  1.73280634  0.57785889  1.5858852   0.49093732  0.46508149
    0.71090896  1.31162119  0.6081533   0.795906    0.66140379  1.45468664
    0.87347307  0.35982942  0.75867436  0.29503668  0.2         0.42730891
    0.39734128  0.68474907  0.27070849  1.09135253  0.99528067  0.62147738
    0.45554969  0.60866561  0.3757151   0.76052526  0.24        1.96136727
    0.45867667  1.69554306  0.5334554   0.33116212  0.58532863  0.59491545
    0.45311729  0.64750618  0.46664234  0.77742232  0.59982206  0.4484523
    0.2         0.67184777  1.4206807   0.31958008  0.45240096  0.9407526
    0.24        0.94460064  0.97453039  0.60548406  0.44192809  0.35467411
    0.32231378  0.93392279  1.12016048  1.21238     0.34737551  0.39613672
    0.95560285  0.623376    0.2         0.59657029]

    References
    ----------
    .. [pagerank_wikipedia] http://en.wikipedia.org/wiki/Pagerank
    .. [lawrence_pagerank_1998] P. Lawrence, B. Sergey, M. Rajeev, W. Terry,
       "The pagerank citation ranking: Bringing order to the web",  Technical
       report, Stanford University, 1998
    """

    if max_iter == None:
        max_iter = 0
    if prop == None:
        prop = g.new_vertex_property("double")
    ic = libgraph_tool_centrality.\
            get_pagerank(g._Graph__graph, _prop("v", g, prop), damping, epslon,
                         max_iter)
    if ret_iter:
        return prop, ic
    else:
        return prop

def betweenness(g, vprop=None, eprop=None, weight=None, norm=True):
    r"""
    Calculate the betweenness centrality for each vertex and edge.

    Parameters
    ----------
    g : Graph
        Graph to be used.
    vprop : ProperyMap, optional (default: None)
        Vertex property map to store the vertex betweenness values.
    eprop : ProperyMap, optional (default: None)
        Edge property map to store the edge betweenness values.
    weight : ProperyMap, optional (default: None)
        Edge property map corresponding to the weight value of each edge.
    norm : bool, optional (default: True)
        Whether or not the betweenness values should be normalized.

    Returns
    -------
    A tuple containing a vertex property map and an edge property map with the
    respective betweenness values.

    See Also
    --------
    central_point_dominance: central point dominance of the graph
    pagerank: PageRank centrality
    eigentrust: eigentrust centrality
    absolute_trust: absolute trust centrality

    Notes
    -----
    Betweenness centrality of a vertex :math:`C_B(v)` is defined as,

    .. math:
        C_B(v)= \sum_{s \neq v \neq t \in V \atop s \neq t}
                \frac{\sigma_{st}(v)}{\sigma_{st}}

    where :math:`\sigma_{st}` is the number of shortest geodesic paths from s to
    t, and :math:`\sigma_{st}(v)` is the number of shortest geodesic paths from
    s to t that pass through a vertex v.  This may be normalised by dividing
    through the number of pairs of vertices not including v, which is
    :math:`(n-1)(n-2)/2`.

    The algorithm used here is defined in _[brandes_faster_2001], and has a
    complexity of :math:`O(VE)` for unweighted graphs and :math:`O(VE + V(V+E)
    \log V)` for weighted graphs. The space complexity is :math:`O(VE)`.

    If enabled during compilation, this algorithm runs in parallel.

    Examples
    --------
    >>> from numpy.random import poisson
    >>> g = gt.random_graph(100, lambda: (poisson(3), poisson(3)), seed=42)
    >>> vb, eb = gt.betweenness(g)
    >>> print vb.get_array()
    [ 0.04156663  0.04437293  0.05111713  0.04426975  0.05518562  0.01015239
    0.          0.02696981  0.00849224  0.01177936  0.03467101  0.01958941
    0.05491377  0.00140963  0.00810379  0.0061649   0.01325843  0.
    0.00388506  0.          0.07004857  0.01540617  0.02101045  0.03078003
    0.02823591  0.01752393  0.          0.0487721   0.04102476  0.02308081
    0.00320094  0.01265714  0.0168692   0.06652112  0.02913082  0.
    0.01509914  0.08867136  0.01399966  0.09695112  0.01803752  0.
    0.01628919  0.10413395  0.00860251  0.          0.          0.06342465
    0.07319201  0.01197855  0.01750122  0.00393044  0.          0.01697703
    0.01301164  0.04819859  0.          0.0284821   0.03074227  0.02090606
    0.02107045  0.03068094  0.01983066  0.02918679  0.00164227  0.06705493
    0.02547069  0.10370115  0.02012076  0.02351567  0.01136589  0.01367043
    0.01392008  0.00634258  0.          0.0530404   0.02245571  0.01590784
    0.          0.03704311  0.05519485  0.00966124  0.0130797   0.01528993
    0.00145159  0.00298564  0.02297654  0.03740528  0.02934682  0.0101206   0.
    0.02320795  0.04883052  0.0322225   0.01573123  0.          0.04031835
    0.05886674  0.          0.01637893]

    References
    ----------
    .. [betweenness_wikipedia] http://en.wikipedia.org/wiki/Centrality#Betweenness_centrality
    .. [brandes_faster_2001] U. Brandes, "A faster algorithm for betweenness
       centrality",  Journal of Mathematical Sociology, 2001
    """
    if vprop == None:
        vprop = g.new_vertex_property("double")
    if eprop == None:
        eprop = g.new_edge_property("double")
    if weight != None and weight.value_type() != eprop.value_type():
        nw = g.new_edge_property(eprop.value_type())
        g.copy_property(weight, nw)
        weight = nw
    libgraph_tool_centrality.\
            get_betweenness(g._Graph__graph, _prop("e", g, weight),
                            _prop("e", g, eprop), _prop("v", g, vprop), norm)
    return vprop, eprop

def central_point_dominance(g, betweenness):
    r"""
    Calculate the central point dominance of the graph, given the betweenness
    centrality of each vertex.

    Parameters
    ----------
    g : Graph
        Graph to be used.
    betweenness : ProperyMap
        Vertex property map with the betweenness centrality values. The values
        must be normalized.

    Returns
    -------
    The central point dominance (float).

    See Also
    --------
    betweenness: betweenness centrality

    Notes
    -----
    Let :math:`v^*` be the vertex with the largest relative betweenness
    centrality; then, the central point dominance _[freeman_set_1977] is defined
    as:

    .. math:
        C'_B = \frac{1}{|V|-1} \sum_{v} C_B(v^*) - C_B(v)

    where :math:`C_B(v)` is the normalized betweenness centrality of vertex
    v. The value of :math:`C_B` lies in the range [0,1].

    The algorithm has a complexity of :math:`O(V)`.

    Examples
    --------
    >>> from numpy.random import poisson
    >>> g = gt.random_graph(100, lambda: (poisson(3), poisson(3)), seed=42)
    >>> vb, eb = gt.betweenness(g)
    >>> print gt.central_point_dominance(g, vb)
    0.138990020139

    References
    ----------
    .. [freeman_set_1977] Linton C. Freeman, "A Set of Measures of Centrality
       Based on Betweenness", Sociometry, Vol. 40, No. 1,  pp. 35-41 (1977)
    """

    return libgraph_tool_centrality.\
           get_central_point_dominance(g._Graph__graph,
                                       _prop("v", g, betweenness))


def eigentrust(g, trust_map, vprop=None, norm=False, epslon=1e-6, max_iter=0,
               ret_iter=False):
    r"""
    Calculate the eigentrust centrality of each vertex in the graph.

    Parameters
    ----------
    g : Graphs
        Graph to be used.
    trust_map : ProperyMap
        Edge property map with the values of trust associated with each
        edge. The values must not lie in the range [0,1].
    vprop : PropertyMap, optional (default: None)
        Vertex property map where the values of eigentrust must be stored.
    norm : bool, optional (default: false)
        Norm eigentrust values so that the total sum equals 1.
    epslon : float, optional (default: 1e-6)
        Convergence condition. The iteration will stop if the total delta of all
        vertices are below this value.
    max_iter : int, optional (default: None)
        If supplied, this will limit the total number of iterations.
    ret_iter : bool, optional (default: False)
        If true, the total number of iterations is also returned.

    Returns
    -------
    A vertex property map containing the eigentrust values.

    See Also
    --------
    betweenness: betweenness centrality
    pagerank: PageRank centrality
    absolute_trust: absolute trust centrality

    Notes
    -----
    The eigentrust _[kamvar_eigentrust_2003] values :math:`t_i` correspond the
    following limit

    .. math:
        \mathbf{t} = \lim_{n\to\infty} \left(C^T\right)^n \mathbf{c}

    where :math:`c_i = 1/|V|` and the elements of the matrix :math:`C` are the
    normalized trust values:

    .. math:
        c_{ij} = \frac{\max(s_{ij},0)}{\sum_{j} \max(s_{ij}, 0)}

    The algorithm has a topology-dependent complexity.

    If enabled during compilation, this algorithm runs in parallel.

    Examples
    --------
    >>> from numpy.random import poisson, random, seed
    >>> seed(42)
    >>> g = gt.random_graph(100, lambda: (poisson(3), poisson(3)), seed=42)
    >>> trust = g.new_edge_property("double")
    >>> trust.get_array()[:] = random(g.num_edges())*42
    >>> t = eigentrust(g, trust, norm=True)
    >>> print t.get_array()
    [  9.48423789e-04   1.66078086e-02   3.24301008e-02   2.51269077e-02
       4.58889062e-03   6.32886469e-03   3.95308763e-03   4.87246882e-03
       5.53852192e-03   9.37363084e-03   1.17843106e-02   2.65124314e-03
       4.47045232e-03   2.51950468e-03   1.59255295e-02   6.03159113e-03
       6.72140367e-03   1.71280616e-03   1.24012407e-02   1.14231095e-02
       9.85151282e-03   5.56192871e-03   6.74797491e-03   2.63245538e-03
       9.21152238e-03   8.16728082e-03   3.98587427e-03   1.70045178e-02
       8.37146815e-03   1.29174460e-02   3.19556744e-03   2.67554442e-03
       1.24085488e-02   1.17337267e-02   3.13424443e-03   1.66366342e-02
       1.25374784e-02   2.65548170e-02   2.17676368e-02   1.73783204e-02
       9.20641085e-03   2.11744591e-02   6.25110430e-03   2.05212010e-03
       1.43759959e-02   1.63283789e-02   3.17898495e-03   8.86981181e-03
       4.94416312e-03   1.24896279e-03   1.07967554e-03   3.54578850e-04
       3.86590892e-04   4.21633271e-02   2.52101241e-03   2.32337004e-02
       1.69840276e-02   1.61722366e-02   7.24752207e-03   1.03185292e-02
       2.04849646e-02   1.94466303e-02   2.01785230e-03   9.31938244e-05
       1.67364460e-02   9.37317475e-03   2.06112300e-03   3.78202160e-03
       9.33152939e-03   5.00810967e-03   6.95505313e-03   2.49521643e-03
       4.53346948e-02   3.74770290e-03   6.78252167e-03   2.55396413e-02
       0.00000000e+00   6.66150362e-03   0.00000000e+00   8.30734676e-03
       9.81158582e-03   1.36569726e-03   1.27503978e-02   1.07028771e-02
       7.91984678e-03   1.81615021e-02   8.05566933e-03   6.71131661e-03
       2.69021984e-02   3.20556792e-03   3.44845723e-03   2.28971468e-04
       1.76318611e-02   1.25007850e-02   1.06310753e-02   1.33265004e-02
       1.10624438e-02   0.00000000e+00   2.00750355e-02   5.37349566e-03]

    References
    ----------
    .. [kamvar_eigentrust_2003] S. D. Kamvar, M. T. Schlosser, H. Garcia-Molina
       "The eigentrust algorithm for reputation management in p2p networks",
       Proceedings of the 12th international conference on World Wide Web,
       Pages: 640 - 651, 2003
    """

    if vprop == None:
        vprop = g.new_vertex_property("double")
    i = libgraph_tool_centrality.\
           get_eigentrust(g._Graph__graph, _prop("e", g, trust_map),
                          _prop("v", g, vprop), epslon, max_iter)
    if norm:
        vprop.get_array()[:] /= sum(vprop.get_array())

    if ret_iter:
        return vprop, i
    else:
        return vprop

def absolute_trust(g, trust_map, vprop=None, epslon=0.1, max_iter=None,
                   seed=None, ret_iter=False)
    r"""
    Samples the absolute trust centrality of each vertex in the graph.

    Parameters
    ----------
    g : Graphs
        Graph to be used.
    trust_map : ProperyMap
        Edge property map with the values of trust associated with each
        edge. The values must lie in the range [0,1].
    vprop : PropertyMap, optional (default: None)
        Vertex property map where the values of eigentrust must be stored.
    epslon : float, optional (default: 0.1)
        Convergence condition. The iteration will stop if the total delta of all
        vertices are below this value.
    max_iter : int, optional (default: None)
        If supplied, this will limit the total number of iterations.
    seed : int, optional (default: None)
         The initializing seed for the random number generator. If not supplied
         a different random value will be chosen each time.
    ret_iter : bool, optional (default: False)
        If true, the total number of iterations is also returned.

    Returns
    -------
    A vertex property map containing the absolute trust vector from the
    corresponding vertex to the rest of the network. Each element i of the
    vector is the trust value of the vertex with index i, from the given vertex.

    See Also
    --------
    eigentrust: eigentrust centrality
    betweenness: betweenness centrality
    pagerank: PageRank centrality

    Notes
    -----
    The absolute trust between vertices i and j is defined as

    .. math:
        t_{ij} = \frac{1}{|\{i\to j\}|}\sum_{\{i\to j\}}
                 \prod_{e\in \{i\to j\}}
                 \frac{c_e^2}{\sum_{w\in\Gamma^+(s(e))}c_{s(e),w}}}

    where the sum is taken over all paths from i to j (without loops), and
    :math:`c_e` is the direct trust value associated with edge e.

    The algorithm progressively samples all possible paths, until the trust
    values converge, and has a topology-dependent complexity.

    If enabled during compilation, this algorithm runs in parallel.

    Examples
    --------
    >>> from numpy.random import poisson, random, seed
    >>> seed(42)
    >>> g = gt.random_graph(100, lambda: (poisson(3), poisson(3)), seed=42)
    >>> trust = g.new_edge_property("double")
    >>> trust.get_array()[:] = random(g.num_edges())
    >>> t = absolute_trust(g, trust)
    >>> print array(t[g.vertex(10)])
    [ 0.00452395  0.00358993  0.00520913  0.00151395  0.09479413  0.00431631
      0.09957709  0.00722076  0.02488298  0.02720262  0.          0.02958085
      0.05583483  0.00525581  0.02112018  0.00157646  0.02070552  0.01317581
      0.01565533  0.00568109  0.04568674  0.00202402  0.0024926   0.14040174
      0.0093484   0.00124116  0.009818    0.039403    0.00787983  0.0130681
      0.02046159  0.02044219  0.00625258  0.00253353  0.00992648  0.00658357
      0.00328796  0.05730617  0.00752433  0.00289023  0.          0.01610246
      0.03151005  0.05449376  0.0195204   0.00296101  0.0187164   0.19553864
      0.01089019  0.01516855  0.01621888  0.29711525  0.00164373  0.02045437
      0.01388174  0.00109321  0.03034565  0.00289681  0.06903929  0.02392237
      0.01491933  0.02128263  0.03091464  0.03457097  0.14454613  0.01821371
      0.00943718  0.0247563   0.00495901  0.03532278  0.00053465  0.
      0.00142457  0.03393286  0.0058909   0.01881276  0.00156345  0.00878983
      0.00832669  0.08389869  0.43991565  0.04075081  0.00323008  0.02823037
      0.03224312  0.00430044  0.0331929   0.00268128  0.01462425  0.00720545
      0.06730403  0.02771813  0.03289217  0.01326689  0.06876157  0.02382899
      0.1502834   0.00980331  0.0086688   0.00495706]
    """

    if seed != 0:
        seed = numpy.random.randint(0, sys.maxint)
    if vprop == None:
        vprop = g.new_vertex_property("vector<double>")
    ic = libgraph_tool_centrality.\
            get_absolute_trust(g._Graph__graph, _prop("e", g, trust_map),
                               _prop("v", g, vprop), epslon, max_iter, seed)
    if ret_iter:
        return vprop, ic
    else:
        return vprop

