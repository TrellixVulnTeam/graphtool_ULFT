// graph-tool -- a general graph modification and manipulation thingy
//
// Copyright (C) 2006-2015 Tiago de Paula Peixoto <tiago@skewed.de>
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

#ifndef HASH_MAP_WRAP_HH
#define HASH_MAP_WRAP_HH

#include "config.h"
#include <unordered_set>
#include <unordered_map>
#include <tuple>
#include <vector>
#include <utility>
#include <limits>

#ifdef HAVE_SPARSEHASH
#include SPARSEHASH_INCLUDE(dense_hash_set)
#include SPARSEHASH_INCLUDE(dense_hash_map)
#endif

template <class Key>
struct no_empty_key : std::exception {};

template <class Key>
struct empty_key
{
    static Key get()
    {
        return dispatch(typename std::is_arithmetic<Key>::type());
    }

    static Key dispatch(std::integral_constant<bool, true>)
    {
        return std::numeric_limits<Key>::max();
    }

    static Key dispatch(std::integral_constant<bool, false>)
    {
        throw no_empty_key<Key>();
    }
};

template <class Key>
struct empty_key<std::vector<Key>>
{
    static std::vector<Key> get()
    {
        return { empty_key<Key>::get() };
    }
};

template <class Val1, class Val2>
struct empty_key<std::pair<Val1, Val2>>
{
    static std::pair<Val1, Val2> get()
    {
        return std::make_pair(empty_key<Val1>::get(),
                              empty_key<Val2>::get());
    }
};


template <class Val, class... Vals>
struct empty_key<std::tuple<Val, Vals...>>
{
    static std::tuple<Val, Vals...> get()
    {
        std::tuple<Val> t = std::make_tuple(empty_key<Val>::get());
        return std::tuple_cat(t, empty_key<std::tuple<Vals...>>::get());
    }
};


template <class Key>
struct no_deleted_key : std::exception {};

template <class Key>
struct deleted_key
{
    static Key get()
    {
        return dispatch(typename std::is_arithmetic<Key>::type());
    }

    static Key dispatch(std::integral_constant<bool, true>)
    {
        if (std::numeric_limits<Key>::is_integer)
            return std::numeric_limits<Key>::max() - 1;
        else
            return std::numeric_limits<Key>::min();
    }

    static Key dispatch(std::integral_constant<bool, false>)
    {
        throw no_deleted_key<Key>();
    }
};

template <class Key>
struct deleted_key<std::vector<Key>>
{
    static std::vector<Key> get()
    {
        return { deleted_key<Key>::get() };
    }
};

template <class Val1, class Val2>
struct deleted_key<std::pair<Val1, Val2>>
{
    static std::pair<Val1, Val2> get()
    {
        return std::make_pair(deleted_key<Val1>::get(),
                              deleted_key<Val2>::get());
    }
};


template <class Val, class... Vals>
struct deleted_key<std::tuple<Val, Vals...>>
{
    static std::tuple<Val, Vals...> get()
    {
        std::tuple<Val> t = std::make_tuple(deleted_key<Val>::get());
        return std::tuple_cat(t, deleted_key<std::tuple<Vals...>>::get());
    }
};

template<class Key,
         class Hash = std::hash<Key>,
         class Pred = std::equal_to<Key>,
         class Alloc = std::allocator<Key>>
class gt_hash_set:
#ifdef HAVE_SPARSEHASH
    public google::dense_hash_set<Key, Hash, Pred, Alloc>
#else
    public std::unordered_set<Key, Hash, Pred, Alloc>
#endif
{
public:
#ifdef HAVE_SPARSEHASH
    typedef google::dense_hash_set<Key, Hash, Pred, Alloc> base_t;
#else
    typedef std::unordered_set<Key, Hash, Pred, Alloc> base_t;
#endif

    gt_hash_set(size_t n = 0,
                const Hash& hf = Hash(),
                const Pred& eql = Pred(),
                const Alloc& alloc = Alloc() )
        : base_t(n, hf, eql, alloc)
    {
#ifdef HAVE_SPARSEHASH
        base_t::set_empty_key(empty_key<Key>::get());
        base_t::set_deleted_key(deleted_key<Key>::get());
#endif
    }

    explicit gt_hash_set (const Alloc& alloc): base_t(alloc) {}

    template <class InputIterator>
    gt_hash_set (InputIterator first, InputIterator last,
                 size_t n = 0,
                 const Hash& hf = Hash(),
                 const Pred& eql = Pred(),
                 const Alloc& alloc = Alloc() )
#ifdef HAVE_SPARSEHASH
        : base_t(first, last, empty_key<Key>::get(), n, hf, eql, alloc)
    {
        base_t::set_deleted_key(deleted_key<Key>::get());
    }
#else
        : base_t(first, last, n, hf, eql, alloc) {}

#endif
    // gt_hash_set(const gt_hash_set& gmp): base_t(gmp) {}
    // gt_hash_set(const gt_hash_set& gmp, Alloc& alloc): base_t(gmp, alloc)  {}
    // gt_hash_set(gt_hash_set&& gmp): base_t(gmp) {}
    // gt_hash_set(gt_hash_set&& gmp, const Alloc& alloc): base_t(gmp, alloc) {}
    gt_hash_set(std::initializer_list<typename base_t::value_type> il,
                size_t n = 0,
                const Hash& hf = Hash(),
                const Pred& eql = Pred(),
                const Alloc& alloc = Alloc() )
#ifdef HAVE_SPARSEHASH
        : base_t(il.begin(), il.end(), empty_key<Key>::get(), n, hf, eql, alloc)
    {
        base_t::set_deleted_key(deleted_key<Key>::get());
    }
#else
        : base_t(il, n, hf, eql, alloc) { }
#endif
};

template<class Key,
         class Value,
         class Hash = std::hash<Key>,
         class Pred = std::equal_to<Key>,
         class Alloc = std::allocator<Key>>
class gt_hash_map:
#ifdef HAVE_SPARSEHASH
    public google::dense_hash_map<Key, Value, Hash, Pred, Alloc>
#else
    public std::unordered_map<Key, Value, Hash, Pred, Alloc>
#endif
{
public:
#ifdef HAVE_SPARSEHASH
    typedef google::dense_hash_map<Key, Value, Hash, Pred, Alloc> base_t;
#else
    typedef std::unordered_map<Key, Value, Hash, Pred, Alloc> base_t;
#endif

    gt_hash_map(size_t n = 0,
                const Hash& hf = Hash(),
                const Pred& eql = Pred(),
                const Alloc& alloc = Alloc() )
        : base_t(n, hf, eql, alloc)
    {
#ifdef HAVE_SPARSEHASH
        base_t::set_empty_key(empty_key<Key>::get());
        base_t::set_deleted_key(deleted_key<Key>::get());
#endif
    }

    explicit gt_hash_map (const Alloc& alloc): base_t(alloc) {}

    template <class InputIterator>
    gt_hash_map (InputIterator first, InputIterator last,
                 size_t n = 0,
                 const Hash& hf = Hash(),
                 const Pred& eql = Pred(),
                 const Alloc& alloc = Alloc() )
#ifdef HAVE_SPARSEHASH
        : base_t(first, last, empty_key<Key>::get(), n, hf, eql, alloc)
    {
        base_t::set_deleted_key(deleted_key<Key>::get());
    }
#else
        : base_t(first, last, n, hf, eql, alloc) {}

#endif
    // gt_hash_map(const gt_hash_map& gmp): base_t(gmp) {}
    // gt_hash_map(const gt_hash_map& gmp, Alloc& alloc): base_t(gmp, alloc)  {}
    // gt_hash_map(gt_hash_map&& gmp): base_t(gmp) {}
    // gt_hash_map(gt_hash_map&& gmp, const Alloc& alloc): base_t(gmp, alloc) {}
    gt_hash_map(std::initializer_list<typename base_t::value_type> il,
                size_t n = 0,
                const Hash& hf = Hash(),
                const Pred& eql = Pred(),
                const Alloc& alloc = Alloc() )
#ifdef HAVE_SPARSEHASH
        : base_t(il.begin(), il.end(), empty_key<Key>::get(), n, hf, eql, alloc)
    {
        base_t::set_deleted_key(deleted_key<Key>::get());
    }
#else
        : base_t(il, n, hf, eql, alloc) { }
#endif
};


#endif // HASH_MAP_WRAP_HH