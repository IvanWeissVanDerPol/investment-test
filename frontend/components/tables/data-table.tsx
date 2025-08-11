"use client"

import React, { useState, useRef, useCallback, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Search,
  Filter,
  Download,
  Settings2,
} from 'lucide-react'

interface Column<T> {
  key: string
  header: string
  accessor: (row: T) => any
  sortable?: boolean
  width?: number
  align?: 'left' | 'center' | 'right'
  render?: (value: any, row: T) => React.ReactNode
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  pageSize?: number
  searchable?: boolean
  filterable?: boolean
  exportable?: boolean
  className?: string
  rowHeight?: number
  virtualScroll?: boolean
  onRowClick?: (row: T) => void
  selectedRow?: T | null
}

type SortDirection = 'asc' | 'desc' | null

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  pageSize = 50,
  searchable = true,
  filterable = true,
  exportable = true,
  className,
  rowHeight = 48,
  virtualScroll = true,
  onRowClick,
  selectedRow,
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)
  const [scrollTop, setScrollTop] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  // Filter and sort data
  const processedData = useMemo(() => {
    let filtered = data

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter((row) =>
        columns.some((col) => {
          const value = col.accessor(row)
          return String(value).toLowerCase().includes(searchTerm.toLowerCase())
        })
      )
    }

    // Sort
    if (sortColumn && sortDirection) {
      const column = columns.find((col) => col.key === sortColumn)
      if (column) {
        filtered = [...filtered].sort((a, b) => {
          const aVal = column.accessor(a)
          const bVal = column.accessor(b)
          
          if (aVal === bVal) return 0
          
          const comparison = aVal < bVal ? -1 : 1
          return sortDirection === 'asc' ? comparison : -comparison
        })
      }
    }

    return filtered
  }, [data, searchTerm, sortColumn, sortDirection, columns])

  // Virtual scrolling calculations
  const containerHeight = 600
  const visibleRows = Math.ceil(containerHeight / rowHeight)
  const startIndex = Math.floor(scrollTop / rowHeight)
  const endIndex = Math.min(startIndex + visibleRows + 1, processedData.length)
  const visibleData = virtualScroll 
    ? processedData.slice(startIndex, endIndex)
    : processedData

  const handleSort = (column: Column<T>) => {
    if (!column.sortable) return

    if (sortColumn === column.key) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortDirection(null)
        setSortColumn(null)
      }
    } else {
      setSortColumn(column.key)
      setSortDirection('asc')
    }
  }

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    if (virtualScroll) {
      setScrollTop(e.currentTarget.scrollTop)
    }
  }, [virtualScroll])

  const exportToCSV = () => {
    const headers = columns.map((col) => col.header).join(',')
    const rows = processedData.map((row) =>
      columns.map((col) => {
        const value = col.accessor(row)
        return typeof value === 'string' && value.includes(',')
          ? `"${value}"`
          : value
      }).join(',')
    )
    const csv = [headers, ...rows].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `data_export_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getSortIcon = (column: Column<T>) => {
    if (!column.sortable) return null
    
    if (sortColumn !== column.key) {
      return <ChevronsUpDown className="h-4 w-4 text-muted-foreground" />
    }
    
    if (sortDirection === 'asc') {
      return <ChevronUp className="h-4 w-4" />
    }
    
    return <ChevronDown className="h-4 w-4" />
  }

  return (
    <div className={cn('rounded-lg border bg-card', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          {searchable && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="h-9 w-64 rounded-lg border border-input bg-background pl-10 pr-3 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
              />
            </div>
          )}
          
          {filterable && (
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <div className="text-sm text-muted-foreground">
            {processedData.length} {processedData.length === 1 ? 'row' : 'rows'}
          </div>
          
          {exportable && (
            <Button variant="outline" size="sm" onClick={exportToCSV}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          )}
          
          <Button variant="outline" size="icon">
            <Settings2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Table */}
      <div 
        ref={containerRef}
        className="overflow-auto"
        style={{ height: `${containerHeight}px` }}
        onScroll={handleScroll}
      >
        <table className="w-full">
          <thead className="sticky top-0 bg-card z-10 border-b">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    'px-4 py-3 text-left text-sm font-medium text-muted-foreground',
                    column.sortable && 'cursor-pointer hover:text-foreground transition-colors',
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right'
                  )}
                  style={{ width: column.width }}
                  onClick={() => handleSort(column)}
                >
                  <div className="flex items-center gap-2">
                    {column.header}
                    {getSortIcon(column)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          
          <tbody>
            {virtualScroll && (
              <tr style={{ height: `${startIndex * rowHeight}px` }}>
                <td colSpan={columns.length} />
              </tr>
            )}
            
            {visibleData.map((row, index) => (
              <tr
                key={startIndex + index}
                className={cn(
                  'border-b transition-colors',
                  onRowClick && 'cursor-pointer hover:bg-accent/50',
                  selectedRow === row && 'bg-accent'
                )}
                style={{ height: `${rowHeight}px` }}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((column) => {
                  const value = column.accessor(row)
                  return (
                    <td
                      key={column.key}
                      className={cn(
                        'px-4 py-2 text-sm',
                        column.align === 'center' && 'text-center',
                        column.align === 'right' && 'text-right'
                      )}
                    >
                      {column.render ? column.render(value, row) : value}
                    </td>
                  )
                })}
              </tr>
            ))}
            
            {virtualScroll && (
              <tr style={{ height: `${(processedData.length - endIndex) * rowHeight}px` }}>
                <td colSpan={columns.length} />
              </tr>
            )}
          </tbody>
        </table>
        
        {processedData.length === 0 && (
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            No data available
          </div>
        )}
      </div>
    </div>
  )
}