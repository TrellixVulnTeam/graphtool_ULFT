#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# graph_tool -- a general graph manipulation python module
#
# Copyright (C) 2006-2018 Tiago de Paula Peixoto <tiago@skewed.de>
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
``graph_tool.spectral`` - Spectral properties
---------------------------------------------

Summary
+++++++

.. autosummary::
   :nosignatures:

   adjacency
   laplacian
   incidence
   transition
   modularity_matrix
   hashimoto

Contents
++++++++
"""

from __future__ import division, absolute_import, print_function

from .. import _degree, _prop, Graph, GraphView, _limit_args, Vector_int64_t, \
    Vector_double
from .. stats import label_self_loops
import numpy
import scipy.sparse
import scipy.sparse.linalg

from .. dl_import import dl_import
dl_import("from . import libgraph_tool_spectral")

__all__ = ["adjacency", "laplacian", "incidence", "transition",
           "modularity_matrix", "hashimoto"]


def adjacency(g, weight=None, index=None):
    r"""Return the adjacency matrix of the graph.

    Parameters
    ----------
    g : :class:`~graph_tool.Graph`
        Graph to be used.
    weight : :class:`~graph_tool.PropertyMap` (optional, default: True)
        Edge property map with the edge weights.
    index : :class:`~graph_tool.PropertyMap` (optional, default: None)
        Vertex property map specifying the row/column indexes. If not provided, the
        internal vertex index is used.

    Returns
    -------
    a : :class:`~scipy.sparse.csr_matrix`
        The (sparse) adjacency matrix.

    Notes
    -----
    The adjacency matrix is defined as

    .. math::

        a_{i,j} =
        \begin{cases}
            1 & \text{if } (j, i) \in E, \\
            2 & \text{if } i = j \text{ and } (i, i) \in E, \\
            0 & \text{otherwise},
        \end{cases}

    where :math:`E` is the edge set.

    In the case of weighted edges, the entry values are multiplied by the weight
    of the respective edge.

    In the case of networks with parallel edges, the entries in the matrix
    become simply the edge multiplicities (or twice them for the diagonal).

    .. note::

        For directed graphs the definition above means that the entry
        :math:`a_{i,j}` corresponds to the directed edge :math:`j\to
        i`. Although this is a typical definition in network and graph theory
        literature, many also use the transpose of this matrix.

    Examples
    --------
    .. testsetup::

       import scipy.linalg
       from pylab import *

    >>> g = gt.collection.data["polblogs"]
    >>> A = gt.adjacency(g)
    >>> ew, ev = scipy.linalg.eig(A.todense())

    >>> figure(figsize=(8, 2))
    <...>
    >>> scatter(real(ew), imag(ew), c=sqrt(abs(ew)), linewidths=0, alpha=0.6)
    <...>
    >>> xlabel(r"$\operatorname{Re}(\lambda)$")
    Text(...)
    >>> ylabel(r"$\operatorname{Im}(\lambda)$")
    Text(...)
    >>> tight_layout()
    >>> savefig("adjacency-spectrum.pdf")

    .. testcode::
       :hide:

       savefig("adjacency-spectrum.svg")

    .. figure:: adjacency-spectrum.*
        :align: center

        Adjacency matrix spectrum for the political blog network.

    References
    ----------
    .. [wikipedia-adjacency] http://en.wikipedia.org/wiki/Adjacency_matrix
    """

    if index is None:
        if g.get_vertex_filter()[0] is not None:
            index = g.new_vertex_property("int64_t")
            index.fa = numpy.arange(g.num_vertices())
        else:
            index = g.vertex_index

    E = g.num_edges() if g.is_directed() else 2 * g.num_edges()

    data = numpy.zeros(E, dtype="double")
    i = numpy.zeros(E, dtype="int32")
    j = numpy.zeros(E, dtype="int32")

    libgraph_tool_spectral.adjacency(g._Graph__graph, _prop("v", g, index),
                                     _prop("e", g, weight), data, i, j)

    if E > 0:
        V = max(g.num_vertices(), max(i.max() + 1, j.max() + 1))
    else:
        V = g.num_vertices()

    m = scipy.sparse.coo_matrix((data, (i,j)), shape=(V, V))
    m = m.tocsr()
    return m


@_limit_args({"deg": ["total", "in", "out"]})
def laplacian(g, deg="total", normalized=False, weight=None, index=None):
    r"""Return the Laplacian matrix of the graph.

    Parameters
    ----------
    g : :class:`~graph_tool.Graph`
        Graph to be used.
    deg : str (optional, default: "total")
        Degree to be used, in case of a directed graph.
    normalized : bool (optional, default: False)
        Whether to compute the normalized Laplacian.
    weight : :class:`~graph_tool.PropertyMap` (optional, default: True)
        Edge property map with the edge weights.
    index : :class:`~graph_tool.PropertyMap` (optional, default: None)
        Vertex property map specifying the row/column indexes. If not provided, the
        internal vertex index is used.

    Returns
    -------
    l : :class:`~scipy.sparse.csr_matrix`
        The (sparse) Laplacian matrix.

    Notes
    -----
    The weighted Laplacian matrix is defined as

    .. math::

        \ell_{ij} =
        \begin{cases}
        \Gamma(v_i) & \text{if } i = j \\
        -w_{ij}     & \text{if } i \neq j \text{ and } (j, i) \in E \\
        0           & \text{otherwise}.
        \end{cases}

    Where :math:`\Gamma(v_i)=\sum_j A_{ij}w_{ij}` is sum of the weights of the
    edges incident on vertex :math:`v_i`. The normalized version is

    .. math::

        \ell_{ij} =
        \begin{cases}
        1         & \text{ if } i = j \text{ and } \Gamma(v_i) \neq 0 \\
        -\frac{w_{ij}}{\sqrt{\Gamma(v_i)\Gamma(v_j)}} & \text{ if } i \neq j \text{ and } (j, i) \in E \\
        0         & \text{otherwise}.
        \end{cases}

    In the case of unweighted edges, it is assumed :math:`w_{ij} = 1`.

    For directed graphs, it is assumed :math:`\Gamma(v_i)=\sum_j A_{ij}w_{ij} +
    \sum_j A_{ji}w_{ji}` if ``deg=="total"``, :math:`\Gamma(v_i)=\sum_j A_{ji}w_{ji}`
    if ``deg=="out"`` or :math:`\Gamma(v_i)=\sum_j A_{ij}w_{ij}` ``deg=="in"``.

    .. note::

        For directed graphs the definition above means that the entry
        :math:`\ell_{i,j}` corresponds to the directed edge :math:`j\to
        i`. Although this is a typical definition in network and graph theory
        literature, many also use the transpose of this matrix.

    Examples
    --------

    .. testsetup::

       import scipy.linalg
       from pylab import *

    >>> g = gt.collection.data["polblogs"]
    >>> L = gt.laplacian(g)
    >>> ew, ev = scipy.linalg.eig(L.todense())

    >>> figure(figsize=(8, 2))
    <...>
    >>> scatter(real(ew), imag(ew), c=sqrt(abs(ew)), linewidths=0, alpha=0.6)
    <...>
    >>> xlabel(r"$\operatorname{Re}(\lambda)$")
    Text(...)
    >>> ylabel(r"$\operatorname{Im}(\lambda)$")
    Text(...)
    >>> tight_layout()
    >>> savefig("laplacian-spectrum.pdf")

    .. testcode::
       :hide:

       savefig("laplacian-spectrum.svg")

    .. figure:: laplacian-spectrum.*
        :align: center

        Laplacian matrix spectrum for the political blog network.

    >>> L = gt.laplacian(g, normalized=True)
    >>> ew, ev = scipy.linalg.eig(L.todense())

    >>> figure(figsize=(8, 2))
    <...>
    >>> scatter(real(ew), imag(ew), c=sqrt(abs(ew)), linewidths=0, alpha=0.6)
    <...>
    >>> xlabel(r"$\operatorname{Re}(\lambda)$")
    Text(...)
    >>> ylabel(r"$\operatorname{Im}(\lambda)$")
    Text(...)
    >>> tight_layout()
    >>> savefig("norm-laplacian-spectrum.pdf")

    .. testcode::
       :hide:

       savefig("norm-laplacian-spectrum.svg")

    .. figure:: norm-laplacian-spectrum.*
        :align: center

        Normalized Laplacian matrix spectrum for the political blog network.

    References
    ----------
    .. [wikipedia-laplacian] http://en.wikipedia.org/wiki/Laplacian_matrix
    """

    if index is None:
        if g.get_vertex_filter()[0] is not None:
            index = g.new_vertex_property("int64_t")
            index.fa = numpy.arange(g.num_vertices())
        else:
            index = g.vertex_index

    V = g.num_vertices()
    nself = int(label_self_loops(g, mark_only=True).a.sum())
    E = g.num_edges() - nself
    if not g.is_directed():
        E *= 2

    N = E + g.num_vertices()
    data = numpy.zeros(N, dtype="double")
    i = numpy.zeros(N, dtype="int32")
    j = numpy.zeros(N, dtype="int32")

    if normalized:
        libgraph_tool_spectral.norm_laplacian(g._Graph__graph, _prop("v", g, index),
                                              _prop("e", g, weight), deg, data, i, j)
    else:
        libgraph_tool_spectral.laplacian(g._Graph__graph, _prop("v", g, index),
                                         _prop("e", g, weight), deg, data, i, j)
    if E > 0:
        V = max(g.num_vertices(), max(i.max() + 1, j.max() + 1))
    else:
        V = g.num_vertices()

    m = scipy.sparse.coo_matrix((data, (i, j)), shape=(V, V))
    m = m.tocsr()
    return m


def incidence(g, vindex=None, eindex=None):
    r"""Return the incidence matrix of the graph.

    Parameters
    ----------
    g : :class:`~graph_tool.Graph`
        Graph to be used.
    vindex : :class:`~graph_tool.PropertyMap` (optional, default: None)
        Vertex property map specifying the row indexes. If not provided, the
        internal vertex index is used.
    eindex : :class:`~graph_tool.PropertyMap` (optional, default: None)
        Edge property map specifying the column indexes. If not provided, the
        internal edge index is used.

    Returns
    -------
    a : :class:`~scipy.sparse.csr_matrix`
        The (sparse) incidence matrix.

    Notes
    -----
    For undirected graphs, the incidence matrix is defined as

    .. math::

        b_{i,j} =
        \begin{cases}
            1 & \text{if vertex } v_i \text{and edge } e_j \text{ are incident}, \\
            0 & \text{otherwise}
        \end{cases}

    For directed graphs, the definition is

    .. math::

        b_{i,j} =
        \begin{cases}
            1 & \text{if edge } e_j \text{ enters vertex } v_i, \\
            -1 & \text{if edge } e_j \text{ leaves vertex } v_i, \\
            0 & \text{otherwise}
        \end{cases}

    Examples
    --------
    .. testsetup::

      gt.seed_rng(42)

    >>> g = gt.random_graph(100, lambda: (2,2))
    >>> m = gt.incidence(g)
    >>> print(m.todense())
    [[-1. -1.  0. ...  0.  0.  0.]
     [ 0.  0.  0. ...  0.  0.  0.]
     [ 1.  0.  0. ...  0.  0.  0.]
     ...
     [ 0.  0. -1. ...  0.  0.  0.]
     [ 0.  0.  0. ...  0.  0.  0.]
     [ 0.  0.  0. ...  0.  0.  0.]]

    References
    ----------
    .. [wikipedia-incidence] http://en.wikipedia.org/wiki/Incidence_matrix
    """

    if vindex is None:
        if g.get_edge_filter()[0] is not None:
            vindex = g.new_vertex_property("int64_t")
            vindex.fa = numpy.arange(g.num_vertices())
        else:
            vindex = g.vertex_index

    if eindex is None:
        if g.get_edge_filter()[0] is not None:
            eindex = g.new_edge_property("int64_t")
            eindex.fa = numpy.arange(g.num_edges())
        else:
            eindex = g.edge_index

    E = g.num_edges()

    if E == 0:
        raise ValueError("Cannot construct incidence matrix for a graph with no edges.")

    data = numpy.zeros(2 * E, dtype="double")
    i = numpy.zeros(2 * E, dtype="int32")
    j = numpy.zeros(2 * E, dtype="int32")

    libgraph_tool_spectral.incidence(g._Graph__graph, _prop("v", g, vindex),
                                     _prop("e", g, eindex), data, i, j)
    m = scipy.sparse.coo_matrix((data, (i,j)))
    m = m.tocsr()
    return m

def transition(g, weight=None, index=None):
    r"""Return the transition matrix of the graph.

    Parameters
    ----------
    g : :class:`~graph_tool.Graph`
        Graph to be used.
    weight : :class:`~graph_tool.PropertyMap` (optional, default: True)
        Edge property map with the edge weights.
    index : :class:`~graph_tool.PropertyMap` (optional, default: None)
        Vertex property map specifying the row/column indexes. If not provided, the
        internal vertex index is used.

    Returns
    -------
    T : :class:`~scipy.sparse.csr_matrix`
        The (sparse) transition matrix.

    Notes
    -----
    The transition matrix is defined as

    .. math::

        T_{ij} = \frac{A_{ij}}{k_j}

    where :math:`k_i = \sum_j A_{ji}`, and :math:`A_{ij}` is the adjacency
    matrix.

    In the case of weighted edges, the values of the adjacency matrix are
    multiplied by the edge weights.

    .. note::

        For directed graphs the definition above means that the entry
        :math:`T_{ij}` corresponds to the directed edge :math:`j\to
        i`. Although this is a typical definition in network and graph theory
        literature, many also use the transpose of this matrix.


    Examples
    --------
    .. testsetup::

       import scipy.linalg
       from pylab import *

    >>> g = gt.collection.data["polblogs"]
    >>> T = gt.transition(g)
    >>> ew, ev = scipy.linalg.eig(T.todense())

    >>> figure(figsize=(8, 2))
    <...>
    >>> scatter(real(ew), imag(ew), c=sqrt(abs(ew)), linewidths=0, alpha=0.6)
    <...>
    >>> xlabel(r"$\operatorname{Re}(\lambda)$")
    Text(...)
    >>> ylabel(r"$\operatorname{Im}(\lambda)$")
    Text(...)
    >>> tight_layout()
    >>> savefig("transition-spectrum.pdf")

    .. testcode::
       :hide:

       savefig("transition-spectrum.svg")

    .. figure:: transition-spectrum.*
        :align: center

        Transition matrix spectrum for the political blog network.

    References
    ----------
    .. [wikipedia-transition] https://en.wikipedia.org/wiki/Stochastic_matrix
    """

    if index is None:
        if g.get_vertex_filter()[0] is not None:
            index = g.new_vertex_property("int64_t")
            index.fa = numpy.arange(g.num_vertices())
        else:
            index = g.vertex_index

    E = g.num_edges() if g.is_directed() else 2 * g.num_edges()
    data = numpy.zeros(E, dtype="double")
    i = numpy.zeros(E, dtype="int32")
    j = numpy.zeros(E, dtype="int32")

    libgraph_tool_spectral.transition(g._Graph__graph, _prop("v", g, index),
                                      _prop("e", g, weight), data, i, j)

    if E > 0:
        V = max(g.num_vertices(), max(i.max() + 1, j.max() + 1))
    else:
        V = g.num_vertices()
    m = scipy.sparse.coo_matrix((data, (i,j)), shape=(V, V))
    m = m.tocsr()
    return m



def modularity_matrix(g, weight=None, index=None):
    r"""Return the modularity matrix of the graph.

    Parameters
    ----------
    g : :class:`~graph_tool.Graph`
        Graph to be used.
    weight : :class:`~graph_tool.PropertyMap` (optional, default: True)
        Edge property map with the edge weights.
    index : :class:`~graph_tool.PropertyMap` (optional, default: None)
        Vertex property map specifying the row/column indexes. If not provided, the
        internal vertex index is used.

    Returns
    -------
    B : :class:`~scipy.sparse.linalg.LinearOperator`
        The (sparse) modularity matrix, represented as a
        :class:`~scipy.sparse.linalg.LinearOperator`.

    Notes
    -----
    The modularity matrix is defined as

    .. math::

        B_{ij} =  A_{ij} - \frac{k^+_i k^-_j}{2E}

    where :math:`k^+_i = \sum_j A_{ji}`, :math:`k^-_i = \sum_j A_{ij}`,
    :math:`2E=\sum_{ij}A_{ij}` and :math:`A_{ij}` is the adjacency matrix.

    In the case of weighted edges, the values of the adjacency matrix are
    multiplied by the edge weights.

    Examples
    --------

    .. testsetup::

       import scipy.linalg
       from pylab import *

    >>> g = gt.collection.data["polblogs"]
    >>> B = gt.modularity_matrix(g)
    >>> B = B * np.identity(B.shape[0])  # transform to a dense matrix
    >>> ew, ev = scipy.linalg.eig(B)

    >>> figure(figsize=(8, 2))
    <...>
    >>> scatter(real(ew), imag(ew), c=sqrt(abs(ew)), linewidths=0, alpha=0.6)
    <...>
    >>> xlabel(r"$\operatorname{Re}(\lambda)$")
    Text(...)
    >>> ylabel(r"$\operatorname{Im}(\lambda)$")
    Text(...)
    >>> tight_layout()
    >>> savefig("modularity-spectrum.pdf")

    .. testcode::
       :hide:

       savefig("modularity-spectrum.svg")

    .. figure:: modularity-spectrum.*
        :align: center

        Modularity matrix spectrum for the political blog network.

    References
    ----------
    .. [newman-modularity]  M. E. J. Newman, M. Girvan, "Finding and evaluating
       community structure in networks", Phys. Rev. E 69, 026113 (2004).
       :doi:`10.1103/PhysRevE.69.026113`
    """

    A = adjacency(g, weight=weight, index=index)
    if g.is_directed():
        k_in = g.degree_property_map("in", weight=weight).fa
    else:
        k_in = g.degree_property_map("out", weight=weight).fa
    k_out = g.degree_property_map("out", weight=weight).fa

    N = A.shape[0]
    E2 = float(k_out.sum())

    def matvec(x):
        M = x.shape[0]
        if len(x.shape) > 1:
            x = x.reshape(M)
        nx = A * x - k_out * numpy.dot(k_in, x) / E2
        return nx

    def rmatvec(x):
        M = x.shape[0]
        if len(x.shape) > 1:
            x = x.reshape(M)
        nx = A.T * x - k_in * numpy.dot(k_out, x) / E2
        return nx

    B = scipy.sparse.linalg.LinearOperator((g.num_vertices(), g.num_vertices()),
                                           matvec=matvec, rmatvec=rmatvec,
                                           dtype="float")

    return B

def hashimoto(g, index=None, compact=False):
    r"""Return the Hashimoto (or non-backtracking) matrix of a graph.

    Parameters
    ----------
    g : :class:`~graph_tool.Graph`
        Graph to be used.
    index : :class:`~graph_tool.PropertyMap` (optional, default: None)
        Edge property map specifying the row/column indexes. If not provided, the
        internal edge index is used.

    Returns
    -------
    H : :class:`~scipy.sparse.csr_matrix`
        The (sparse) Hashimoto matrix.

    Notes
    -----
    The Hashimoto (a.k.a. non-backtracking) matrix is defined as

    .. math::

        h_{k\to l,i\to j} =
        \begin{cases}
            1 & \text{if } (k,l) \in E, (i,j) \in E, l=i, k\ne j,\\
            0 & \text{otherwise},
        \end{cases}

    where :math:`E` is the edge set. It is therefore a :math:`2|E|\times 2|E|`
    asymmetric square matrix (or :math:`|E|\times |E|` for directed graphs),
    indexed over edge directions.

    If the option ``compact=True`` is passed, the matrix returned has shape
    :math:`2|V|\times 2|V|`, where :math:`|V|` is the number of vertices, and is
    given by

    .. math::

        \boldsymbol h =
        \left(\begin{array}{c|c}
            \boldsymbol A & -\boldsymbol 1 \\ \hline
            \boldsymbol D-\boldsymbol 1 & \boldsymbol 0
        \end{array}\right)

    where :math:`\boldsymbol A` is the adjacency matrix, and :math:`\boldsymbol
    D` is the diagonal matrix with the node degrees.

    Examples
    --------
    .. testsetup::

       import scipy.linalg
       from pylab import *

    >>> g = gt.collection.data["football"]
    >>> H = gt.hashimoto(g)
    >>> ew, ev = scipy.linalg.eig(H.todense())
    >>> figure(figsize=(8, 4))
    <...>
    >>> scatter(real(ew), imag(ew), c=sqrt(abs(ew)), linewidths=0, alpha=0.6)
    <...>
    >>> xlabel(r"$\operatorname{Re}(\lambda)$")
    Text(...)
    >>> ylabel(r"$\operatorname{Im}(\lambda)$")
    Text(...)
    >>> tight_layout()
    >>> savefig("hashimoto-spectrum.pdf")

    .. testcode::
       :hide:

       savefig("hashimoto-spectrum.svg")

    .. figure:: hashimoto-spectrum.*
        :align: center

        Hashimoto matrix spectrum for the network of American football teams.

    References
    ----------
    .. [hashimoto] Hashimoto, Ki-ichiro. "Zeta functions of finite graphs and
       representations of p-adic groups." Automorphic forms and geometry of
       arithmetic varieties. 1989. 211-280. :DOI:`10.1016/B978-0-12-330580-0.50015-X`
    .. [krzakala_spectral] Florent Krzakala, Cristopher Moore, Elchanan Mossel,
       Joe Neeman, Allan Sly, Lenka Zdeborová, and Pan Zhang, "Spectral redemption
       in clustering sparse networks", PNAS 110 (52) 20935-20940, 2013.
       :doi:`10.1073/pnas.1312486110`, :arxiv:`1306.5550`
    """

    if compact:
        i = Vector_int64_t()
        j = Vector_int64_t()
        x = Vector_double()

        libgraph_tool_spectral.compact_nonbacktracking(g._Graph__graph,
                                                       i, j, x)

        N = g.num_vertices(ignore_filter=True)
        m = scipy.sparse.coo_matrix((x, (i.a,j.a)), shape=(2 * N, 2 * N))
    else:
        if index is None:
            if g.get_edge_filter()[0] is not None:
                index = g.new_edge_property("int64_t")
                index.fa = numpy.arange(g.num_edges())
                E = index.fa.max() + 1
            else:
                index = g.edge_index
                E = g.edge_index_range

        if not g.is_directed():
            E *= 2

        i = Vector_int64_t()
        j = Vector_int64_t()

        libgraph_tool_spectral.nonbacktracking(g._Graph__graph, _prop("e", g, index),
                                               i, j)

        data = numpy.ones(i.a.shape)
        m = scipy.sparse.coo_matrix((data, (i.a,j.a)), shape=(E, E))
    m = m.tocsr()
    return m
