// graph-tool -- a general graph modification and manipulation thingy
//
// Copyright (C) 2007  Tiago de Paula Peixoto <tiago@forked.de>
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 3
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

#include "graph_filtering.hh"

#include <boost/python.hpp>
#include <boost/lambda/bind.hpp>
#include <boost/graph/betweenness_centrality.hpp>

#include "graph.hh"
#include "graph_selectors.hh"
#include "graph_util.hh"

using namespace std;
using namespace boost;
using namespace boost::lambda;
using namespace graph_tool;

template <class Graph, class EdgeBetweenness, class VertexBetweenness>
void normalize_betweenness(const Graph& g,
                           EdgeBetweenness edge_betweenness,
                           VertexBetweenness vertex_betweenness,
                           size_t n)
{
    double vfactor = (n > 2) ? 1.0/((n-1)*(n-2)) : 1.0;
    double efactor = (n > 1) ? 1.0/(n*(n-1)) : 1.0;
    if (is_convertible<typename graph_traits<Graph>::directed_category,
                       undirected_tag>::value)
    {
        vfactor *= 2;
        efactor *= 2;
    }

    int i, N = num_vertices(g);
    #pragma omp parallel for default(shared) private(i)   \
        schedule(dynamic)
    for (i = 0; i < N; ++i)
    {
        typename graph_traits<Graph>::vertex_descriptor v = vertex(i, g);
        if (v == graph_traits<Graph>::null_vertex())
            continue;
        put(vertex_betweenness, v, vfactor * get(vertex_betweenness, v));
    }

    typename graph_traits<Graph>::edge_iterator e, e_end;
    for (tie(e, e_end) = edges(g); e != e_end; ++e)
    {
        put(edge_betweenness, *e, efactor * get(edge_betweenness, *e));
    }
}

struct get_betweenness
{
    template <class Graph, class EdgeBetweenness, class VertexBetweenness>
    void operator()(Graph* gp,
                    GraphInterface::vertex_index_map_t index_map,
                    EdgeBetweenness edge_betweenness,
                    VertexBetweenness vertex_betweenness,
                    bool normalize, size_t n) const
    {
        vector<vector<typename graph_traits<Graph>::edge_descriptor> >
            incoming_map(num_vertices(*gp));
        vector<size_t> distance_map(num_vertices(*gp));
        vector<typename property_traits<VertexBetweenness>::value_type>
            dependency_map(num_vertices(*gp));
        vector<size_t> path_count_map(num_vertices(*gp));

        brandes_betweenness_centrality
            (*gp, vertex_betweenness, edge_betweenness,
             make_iterator_property_map(incoming_map.begin(), index_map),
             make_iterator_property_map(distance_map.begin(), index_map),
             make_iterator_property_map(dependency_map.begin(), index_map),
             make_iterator_property_map(path_count_map.begin(), index_map),
             index_map);
        if (normalize)
            normalize_betweenness(*gp, edge_betweenness, vertex_betweenness, n);
    }
};

struct get_weighted_betweenness
{
    template <class Graph, class EdgeBetweenness, class VertexBetweenness,
              class VertexIndexMap>
        void operator()(Graph* gp, VertexIndexMap vertex_index,
                        EdgeBetweenness edge_betweenness,
                        VertexBetweenness vertex_betweenness,
                        boost::any weight_map, bool normalize,
                        size_t n) const
    {
        vector<vector<typename graph_traits<Graph>::edge_descriptor> >
            incoming_map(num_vertices(*gp));
        vector<typename property_traits<EdgeBetweenness>::value_type>
            distance_map(num_vertices(*gp));
        vector<typename property_traits<VertexBetweenness>::value_type>
            dependency_map(num_vertices(*gp));
        vector<size_t> path_count_map(num_vertices(*gp));

        brandes_betweenness_centrality
            (*gp, vertex_betweenness, edge_betweenness,
             make_iterator_property_map(incoming_map.begin(), vertex_index),
             make_iterator_property_map(distance_map.begin(), vertex_index),
             make_iterator_property_map(dependency_map.begin(), vertex_index),
             make_iterator_property_map(path_count_map.begin(), vertex_index),
             vertex_index, any_cast<EdgeBetweenness>(weight_map));
        if (normalize)
            normalize_betweenness(*gp, edge_betweenness, vertex_betweenness, n);
    }
};

void betweenness(GraphInterface& g, boost::any weight,
                 boost::any edge_betweenness,
                 boost::any vertex_betweenness,
                 bool normalize)
{
    if (!belongs<edge_floating_properties>()(edge_betweenness))
        throw GraphException("edge property must be of floating point value type");

    if (!belongs<vertex_floating_properties>()(vertex_betweenness))
        throw GraphException("vertex property must be of floating point value type");

    if (!weight.empty())
    {
        run_action<>()
            (g, lambda::bind<void>
             (get_weighted_betweenness(), lambda::_1, g.GetVertexIndex(),
              lambda::_2, lambda::_3, weight, normalize,
              g.GetNumberOfVertices()),
             edge_floating_properties(),
             vertex_floating_properties())
            (edge_betweenness, vertex_betweenness);
    }
    else
    {
        run_action<>()
            (g, lambda::bind<void>
             (get_betweenness(), lambda::_1, g.GetVertexIndex(), lambda::_2,
              lambda::_3, normalize, g.GetNumberOfVertices()),
             edge_floating_properties(),
             vertex_floating_properties())
            (edge_betweenness, vertex_betweenness);
    }
}

struct get_central_point_dominance
{
    template <class Graph, class VertexBetweenness>
    void operator()(Graph* g, VertexBetweenness vertex_betweenness, double& c)
        const
    {
        c = central_point_dominance(*g, vertex_betweenness);
    }
};

double central_point(GraphInterface& g,
                     boost::any vertex_betweenness)
{
    double c = 0.0;
    run_action<graph_tool::detail::never_reversed>()
        (g, lambda::bind<void>(get_central_point_dominance(), lambda::_1,
                               lambda::_2, var(c)),
         vertex_scalar_properties()) (vertex_betweenness);
    return c;
}

void export_betweenness()
{
    using namespace boost::python;
    def("get_betweenness", &betweenness);
    def("get_central_point_dominance", &central_point);
}
